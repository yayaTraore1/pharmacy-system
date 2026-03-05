from fastapi import APIRouter, Depends, HTTPException, Form, Request, Query
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.models.supplier import Supplier
from app.utils.dependencies import require_role, get_current_user
from datetime import datetime
from sqlalchemy import or_
from app.utils.pdf_report import generate_products_pdf


router = APIRouter(prefix="/products", tags=["Products"])
templates = Jinja2Templates(directory="templates")


# =====================================================
# 📄 PAGE LISTE PRODUITS
# =====================================================
@router.get("/page")
def products_page(
    request: Request,
    search: str = Query(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    query = db.query(Product).join(Supplier, isouter=True)

    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Supplier.name.ilike(f"%{search}%")
            )
        )

    products = query.all()

    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "products": products,
            "search": search,
            "user": user
        }
    )
# =====================================================
# ➕ PAGE CREATE PRODUIT
# =====================================================
@router.get("/create")
def create_product_page(
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    suppliers = db.query(Supplier).all()

    return templates.TemplateResponse(
        "product_create.html",
        {
            "request": request,
            "suppliers": suppliers,
            "user": user
        }
    )


# =====================================================
# ✏ PAGE EDIT PRODUIT
# =====================================================
@router.get("/edit/{product_id}")
def product_edit_page(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    suppliers = db.query(Supplier).all()

    return templates.TemplateResponse(
        "product_edit.html",
        {
            "request": request,
            "product": product,
            "suppliers": suppliers,
            "user": user
        }
    )


# =====================================================
# 💾 CREATE PRODUCT
# =====================================================
@router.post("/")
def create_product(
    name: str = Form(...),
    quantity: int = Form(...),
    sale_price: float = Form(...),
    supplier_id: int = Form(...),
    expiration_date: str = Form(...),
    rupture_threshold: int = Form(...),
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    purchase_price = sale_price / 1.4

    new_product = Product(
        name=name,
        quantity=quantity,
        sale_price=sale_price,
        purchase_price=purchase_price,
        supplier_id=supplier_id,
        expiration_date=datetime.strptime(expiration_date, "%Y-%m-%d"),
        rupture_threshold=rupture_threshold
    )

    db.add(new_product)
    db.commit()

    return RedirectResponse("/products/page", status_code=303)


# =====================================================
# 🔄 UPDATE PRODUCT
# =====================================================
@router.post("/edit/{product_id}")
def edit_product(
    product_id: int,
    name: str = Form(...),
    quantity: int = Form(...),
    sale_price: float = Form(...),
    supplier_id: int = Form(...),
    expiration_date: str = Form(...),
    rupture_threshold: int = Form(...),
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    product.name = name
    product.quantity = quantity
    product.sale_price = sale_price
    product.purchase_price = sale_price / 1.4
    product.supplier_id = supplier_id
    product.expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d")
    product.rupture_threshold = rupture_threshold

    db.commit()

    return RedirectResponse("/products/page", status_code=303)


# =====================================================
# 🗑 DELETE PRODUCT
# =====================================================
@router.get("/delete/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    db.delete(product)
    db.commit()

    return RedirectResponse("/products/page", status_code=303)


# =====================================================
# 📄 EXPORT PDF
# =====================================================
@router.get("/export-pdf")
def export_products_pdf(
    search: str = Query(None),
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    query = db.query(Product).join(Supplier, isouter=True)

    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Supplier.name.ilike(f"%{search}%")
            )
        )

    products = query.all()

    # génère un PDF structuré et professionnel via utilitaire
    filepath = generate_products_pdf(products)
    return FileResponse(filepath, media_type="application/pdf", filename="produits.pdf")