from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta

from app.database import get_db
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.user import User
from app.utils.dependencies import get_current_user
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

templates = Jinja2Templates(directory="templates")


@router.get("/")
def dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)):

    today = date.today()

    # ===============================
    # PRODUITS EN RUPTURE
    # ===============================
    rupture_products = db.query(Product).filter(
        Product.quantity <= Product.rupture_threshold
    ).all()

    # ===============================
    # PRODUITS EXPIRÉS & BIENTÔT EXPIRÉS
    # ===============================
    limit_date = today + timedelta(days=30)
    
    expired_products = db.query(Product).filter(
        Product.expiration_date <= today
    ).all()
    
    expired_soon_products = db.query(Product).filter(
        Product.expiration_date <= limit_date,
        Product.expiration_date > today
    ).all()
    
    # Ajouter statut à chaque produit
    for p in expired_products:
        p.expiration_status = "Expiré"
    for p in expired_soon_products:
        p.expiration_status = "Bientôt expiré"
    
    # Combiner les listes
    all_expiration_products = expired_products + expired_soon_products
    all_expiration_products = sorted(all_expiration_products, key=lambda x: x.expiration_date)   

    # ===============================
    # TOTAL PRODUITS
    # ===============================
    total_products = db.query(Product).count()

    # ===============================
    # TOTAL VENTES AUJOURD'HUI
    # ===============================
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    today_sales = db.query(Sale).filter(
        Sale.created_at >= today_start,
        Sale.created_at <= today_end,
        Sale.is_cancelled == False
    ).all()

    today_sales_total = sum(s.total_amount for s in today_sales)

    # ===============================
    # BENEFICE AUJOURD'HUI
    # ===============================
    profit_today = 0

    for sale in today_sales:
        for item in sale.items:
            purchase_price = item.product.purchase_price or 0
            profit_today += (
                (item.unit_price - purchase_price)
                * item.quantity
            )

    # ===============================
    # TOTAL GLOBAL DES VENTES
    # ===============================
    total_sales_global = db.query(
        func.sum(Sale.total_amount)
    ).filter(
        Sale.is_cancelled == False
    ).scalar() or 0

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "rupture_products": rupture_products,
            "expired_products": expired_products,
            "total_products": total_products,
            "today_sales_total": today_sales_total,
            "profit_today": profit_today,
            "total_sales_global": total_sales_global,
            "expiration_products": all_expiration_products,
            "expired_count": len(expired_products),
            "expired_soon_count": len(expired_soon_products)
        }
    )