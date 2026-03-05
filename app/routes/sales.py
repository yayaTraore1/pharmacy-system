from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func,extract
from datetime import date, datetime, timedelta, timezone

from app.database import get_db
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.product import Product
from app.models.user import User
from app.schemas import user
from app.schemas.sale import SaleCreate
from app.utils.dependencies import get_current_user
from app.utils.invoice import generate_invoice

router = APIRouter(prefix="/sales", tags=["Sales"])
templates = Jinja2Templates(directory="templates")

# =========================================================
# ======================== API =============================
# =========================================================

# CREATE SALE
@router.post("/")
def create_sale(
    sale_data: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not sale_data.items:
        raise HTTPException(status_code=400, detail="Impossible d'enregistrer une vente vide")

    total_amount = 0
    products_cache = []

    for item in sale_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()

        if not product:
            raise HTTPException(status_code=404, detail=f"Produit ID {item.product_id} introuvable")

        if product.quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Stock insuffisant pour {product.name}")

        products_cache.append((product, item.quantity))

    new_sale = Sale(user_id=current_user.id)
    db.add(new_sale)
    db.flush()

    for product, quantity in products_cache:
        total_price = product.sale_price * quantity

        sale_item = SaleItem(
            sale_id=new_sale.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.sale_price,
            total_price=total_price
        )

        db.add(sale_item)
        product.quantity -= quantity
        total_amount += total_price

    new_sale.total_amount = total_amount

    db.commit()
    db.refresh(new_sale)

    return {
        "message": "Vente enregistrée avec succès",
        "sale_id": new_sale.id,
        "total": total_amount
    }

# LISTE API
@router.get("/api")
def get_sales_api(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.query(Sale).filter(
        Sale.is_cancelled == False
    ).order_by(Sale.created_at.desc()).all()

# DETAIL API
@router.get("/api/{sale_id}")
def get_sale_detail_api(
    sale_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not sale:
        raise HTTPException(status_code=404, detail="Vente introuvable")

    return sale

# TELECHARGER FACTURE
@router.get("/{sale_id}/invoice")
def download_invoice(
    sale_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not sale:
        raise HTTPException(status_code=404, detail="Vente introuvable")

    if sale.is_cancelled:
        raise HTTPException(status_code=400, detail="Impossible de générer facture pour une vente annulée")

    items = db.query(SaleItem).filter(
        SaleItem.sale_id == sale_id
    ).all()

    filename = f"facture_{sale_id}.pdf"
    filepath = generate_invoice(sale, items, filename)

    return FileResponse(filepath, media_type="application/pdf", filename=filename)

# ANNULER VENTE
@router.post("/{sale_id}/cancel")
def cancel_sale(sale_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not sale:
        raise HTTPException(status_code=404, detail="Vente introuvable")

    # si elle est déjà annulée, on ne fait rien
    if sale.is_cancelled:
        return RedirectResponse(
            url=f"/sales?alert=deja_annule",
            status_code=status.HTTP_303_SEE_OTHER
        )

    now = datetime.now(timezone.utc)
    created_at = sale.created_at

    # Correction timezone
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    # la règle des 24 heures s'applique uniquement aux ventes non annulées
    if now - created_at > timedelta(hours=24):
        return RedirectResponse(
            url=f"/sales?alert=annulation_24h",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # restaurer les quantités dans le stock
    for item in sale.items:
        item.product.quantity += item.quantity

    sale.is_cancelled = True
    db.commit()

    return RedirectResponse(
        url=f"/sales/?alert=annule",
        status_code=status.HTTP_303_SEE_OTHER
    )

# RESTAURER VENTE
@router.post("/{sale_id}/restaure")
def restaure_sale(sale_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not sale:
        raise HTTPException(status_code=404, detail="Vente introuvable")

    # on ne restaure qu'une vente annulée
    if not sale.is_cancelled:
        return RedirectResponse(
            url=f"/sales/?alert=deja_active",
            status_code=status.HTTP_303_SEE_OTHER
        )

    now = datetime.now(timezone.utc)
    created_at = sale.created_at

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    if now - created_at > timedelta(hours=24):
        return RedirectResponse(
            url=f"/sales/?alert=restaure_24h",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # vérifier qu'il reste bien le stock nécessaire pour re-déduire
    for item in sale.items:
        if item.product.quantity < item.quantity:
            # impossible de restaurer, le stock a été vendu entre temps
            return RedirectResponse(
                url=f"/sales/?alert=stock_insuffisant",
                status_code=status.HTTP_303_SEE_OTHER
            )

    # répercuter dans le stock et ré-activer la vente
    for item in sale.items:
        item.product.quantity -= item.quantity

    sale.is_cancelled = False
    db.commit()

    return RedirectResponse(
        url=f"/sales/?alert=restaure",
        status_code=status.HTTP_303_SEE_OTHER)

# =========================================================
# ======================== HTML ============================
# =========================================================

# PAGE PRINCIPALE
@router.get("/")
def sales_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    sales = db.query(Sale).order_by(Sale.created_at.desc()).all()

    return templates.TemplateResponse("sales.html", {
        "request": request,
        "sales": sales,
        "user": user
    })
# PAGE CREATION
@router.get("/create")
def create_sale_page(request: Request,db: Session = Depends(get_db),user: User = Depends(get_current_user)):

    products = db.query(Product).filter(Product.quantity > 0).all()

    return templates.TemplateResponse("sales_create.html", {
        "request": request,
        "products": products,
        "user": user
    })

# DASHBOARD
@router.get("/dashboard")
def sales_dashboard(request: Request,
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    # Seul les admins peuvent accéder au dashboard
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    today = date.today()
    current_year = today.year
    current_month = today.month

    # =============================
    # TOTAL DU JOUR (VALIDÉES)
    # =============================
    total_today = db.query(func.sum(Sale.total_amount))\
        .filter(func.date(Sale.created_at) == today)\
        .filter(Sale.is_cancelled == False)\
        .scalar() or 0

    # =============================
    # BENEFICE DU JOUR
    # =============================
    profit_today_raw = db.query(
        func.sum(
            (SaleItem.unit_price - Product.purchase_price) * SaleItem.quantity
        )
    ).join(Product, Product.id == SaleItem.product_id)\
     .join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(func.date(Sale.created_at) == today)\
     .filter(Sale.is_cancelled == False)\
     .scalar() or 0
    
    profit_today = round(profit_today_raw, 2)

    # =============================
    # TOTAL GENERAL VALIDÉ
    # =============================
    total_validated = db.query(func.sum(Sale.total_amount))\
        .filter(Sale.is_cancelled == False)\
        .scalar() or 0

    # =============================
    # TOTAL ANNULÉ
    # =============================
    total_cancelled = db.query(func.sum(Sale.total_amount))\
        .filter(Sale.is_cancelled == True)\
        .scalar() or 0

    # =============================
    # TOTAL PAR MOIS (MOIS ACTUEL)
    # =============================
    total_month = db.query(func.sum(Sale.total_amount))\
        .filter(extract('year', Sale.created_at) == current_year)\
        .filter(extract('month', Sale.created_at) == current_month)\
        .filter(Sale.is_cancelled == False)\
        .scalar() or 0

    # =============================
    # TOTAL PAR ANNEE
    # =============================
    total_year = db.query(func.sum(Sale.total_amount))\
        .filter(extract('year', Sale.created_at) == current_year)\
        .filter(Sale.is_cancelled == False)\
        .scalar() or 0

    # =============================
    # VENTES PAR UTILISATEUR
    # =============================
    user_sales = db.query(
        User.username.label("username"),
        func.count(Sale.id).label("count"),
        func.sum(Sale.total_amount).label("total")
    ).join(Sale, Sale.user_id == User.id)\
     .filter(Sale.is_cancelled == False)\
     .group_by(User.username)\
     .all()

    # =============================
    # VENTES DU JOUR PAR UTILISATEUR
    # =============================
    daily_user_sales = db.query(
        User.username.label("username"),
        func.sum(Sale.total_amount).label("total")
    ).join(Sale, Sale.user_id == User.id)\
     .filter(func.date(Sale.created_at) == today)\
     .filter(Sale.is_cancelled == False)\
     .group_by(User.username)\
     .all()

    return templates.TemplateResponse("sales_dashboard.html", {
        "request": request,
        "user": user,
        "total_today": total_today,
        "profit_today": profit_today,
        "total_validated": total_validated,
        "total_cancelled": total_cancelled,
        "total_month": total_month,
        "total_year": total_year,
        "user_sales": user_sales,
        "daily_user_sales": daily_user_sales
    })
# HISTORIQUE HTML
@router.get("/history")
def sales_history(request: Request,
                  date_from: str = None,
                  date_to: str = None,
                  db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):

    query = db.query(Sale)

    if date_from:
        date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
        query = query.filter(Sale.created_at >= date_from_obj)

    if date_to:
        date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
        query = query.filter(Sale.created_at <= date_to_obj)

    sales = query.order_by(Sale.created_at.desc()).all()

    return templates.TemplateResponse("sales_history.html", {
        "request": request,
        "user": user,
        "sales": sales
    })
# =========================================================
# ===== ROUTE DYNAMIQUE EN DERNIER (IMPORTANT !) ==========
# =========================================================

@router.get("/{sale_id}")
def sales_detail_page(
    sale_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not sale:
        raise HTTPException(status_code=404, detail="Vente non trouvée")

    return templates.TemplateResponse("sales_detail.html", {
        "request": request,
        "sale": sale,
        "user": user
    })