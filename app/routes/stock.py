from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.database import get_db
from app.models.product import Product
from app.models.user import User
from app.models.supplier import Supplier
from app.utils.dependencies import get_current_user
from app.utils.pdf_report import generate_ruptures_pdf, generate_expirations_pdf, generate_expired_soon_pdf
from fastapi.templating import Jinja2Templates
from datetime import date,timedelta

router = APIRouter(prefix="/stock", tags=["Stock"])

templates = Jinja2Templates(directory="templates")


# ===========================
# PRODUITS EN RUPTURE
# ===========================
@router.get("/ruptures/page")
def ruptures_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    search: str = None
):

    query = db.query(Product).filter(
        Product.quantity <= Product.rupture_threshold
    )
    
    # Filtre par recherche (nom du produit OU fournisseur)
    if search:
        query = query.outerjoin(Supplier).filter(
            or_(
                func.lower(Product.name).contains(func.lower(search)),
                func.lower(Supplier.name).contains(func.lower(search))
            )
        )

    products = query.order_by(Product.quantity.asc()).all()

    return templates.TemplateResponse("ruptures.html", {
        "request": request,
        "products": products,
        "user": user,
        "search": search
    })


# ===========================
# PRODUITS EXPIRÉS & BIENTÔT EXPIRÉS
# ===========================
@router.get("/expirations/page")
def expirations_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    search: str = None,
    status: str = None
):

    today = date.today()
    limit_date = today + timedelta(days=30)

    expired_query = db.query(Product).filter(
        Product.expiration_date <= today
    )

    expired_soon_query = db.query(Product).filter(
        Product.expiration_date > today,
        Product.expiration_date <= limit_date
    )

    # recherche par nom
    if search:
        expired_query = expired_query.filter(
            func.lower(Product.name).contains(func.lower(search))
        )

        expired_soon_query = expired_soon_query.filter(
            func.lower(Product.name).contains(func.lower(search))
        )

    # filtre par statut
    if status == "expired":

        products = expired_query.order_by(Product.expiration_date.asc()).all()

        for p in products:
            p.expiration_status = "Expiré"

    elif status == "soon":

        products = expired_soon_query.order_by(Product.expiration_date.asc()).all()

        for p in products:
            p.expiration_status = "Bientôt expiré"

    else:

        expired_products = expired_query.order_by(Product.expiration_date.asc()).all()
        expired_soon_products = expired_soon_query.order_by(Product.expiration_date.asc()).all()

        for p in expired_products:
            p.expiration_status = "Expiré"

        for p in expired_soon_products:
            p.expiration_status = "Bientôt expiré"

        products = expired_products + expired_soon_products
        products = sorted(products, key=lambda x: x.expiration_date)

    return templates.TemplateResponse("expirations.html", {
        "request": request,
        "products": products,
        "user": user,
        "search": search,
        "status": status
    })
# ==========================
# Export PDF
# ==========================
@router.get("/ruptures/export-pdf")
def export_ruptures_pdf(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    search: str = None
):
    query = db.query(Product).filter(
        Product.quantity <= Product.rupture_threshold
    )
    
    if search:
        query = query.filter(
            func.lower(Product.name).contains(func.lower(search))
        )

    products = query.order_by(Product.quantity.asc()).all()
    
    filepath = generate_ruptures_pdf(products)
    return FileResponse(filepath, media_type="application/pdf", filename="ruptures.pdf")


@router.get("/expirations/export-pdf")
def export_expirations_pdf(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    search: str = None,
    status: str = None
):

    today = date.today()
    limit_date = today + timedelta(days=30)

    expired_query = db.query(Product).filter(
        Product.expiration_date <= today
    )

    expired_soon_query = db.query(Product).filter(
        Product.expiration_date > today,
        Product.expiration_date <= limit_date
    )

    # recherche par nom
    if search:
        expired_query = expired_query.filter(
            func.lower(Product.name).contains(func.lower(search))
        )

        expired_soon_query = expired_soon_query.filter(
            func.lower(Product.name).contains(func.lower(search))
        )

    # filtre statut
    if status == "expired":

        products = expired_query.order_by(Product.expiration_date.asc()).all()

        for p in products:
            p.expiration_status = "Expiré"

    elif status == "soon":

        products = expired_soon_query.order_by(Product.expiration_date.asc()).all()

        for p in products:
            p.expiration_status = "Bientôt expiré"

    else:

        expired_products = expired_query.order_by(Product.expiration_date.asc()).all()
        expired_soon_products = expired_soon_query.order_by(Product.expiration_date.asc()).all()

        for p in expired_products:
            p.expiration_status = "Expiré"

        for p in expired_soon_products:
            p.expiration_status = "Bientôt expiré"

        products = expired_products + expired_soon_products
        products = sorted(products, key=lambda x: x.expiration_date)

    filepath = generate_expirations_pdf(products)

    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename="rapport_expirations.pdf"
    )

# ===========================
# API JSON (OPTIONNEL)
# ===========================
@router.get("/ruptures")
def get_rupture_products(db: Session = Depends(get_db)):
    return db.query(Product).filter(
        Product.quantity <= Product.rupture_threshold
    ).all()


@router.get("/expirations")
def get_expired_products(db: Session = Depends(get_db)):
    today = date.today()
    return db.query(Product).filter(
        Product.expiration_date <= today
    ).all()

@router.get("/expired_soon")
def get_expired_soon_products(db: Session = Depends(get_db)):
    today = date.today()
    limit_date = today + timedelta(days=30)
    return db.query(Product).filter(
        Product.expiration_date > today,
        Product.expiration_date <= limit_date
    ).all()