from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.supplier import Supplier
from app.utils.dependencies import require_role, get_current_user
from fastapi.responses import FileResponse
from fastapi import UploadFile, File
from app.models.supplier_invoice import SupplierInvoice
import os
import shutil
import uuid
from fastapi import Request
from fastapi.templating import Jinja2Templates


router = APIRouter(prefix="/suppliers", tags=["Suppliers"])
templates = Jinja2Templates(directory="templates")

# =========================
# CREATE SUPPLIER (ADMIN)
# =========================
@router.post("/")
def create_supplier(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    address: str = Form(...),
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    new_supplier = Supplier(
        name=name,
        phone=phone,
        email=email,
        address=address
    )

    db.add(new_supplier)
    db.commit()

    return RedirectResponse("/suppliers/page", status_code=303)


# =========================
# UPDATE SUPPLIER (ADMIN)
# =========================
@router.post("/update/{supplier_id}")
def update_supplier(
    supplier_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    address: str = Form(...),
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur introuvable")

    supplier.name = name
    supplier.phone = phone
    supplier.email = email
    supplier.address = address

    db.commit()

    return RedirectResponse("/suppliers/page", status_code=303)


# =========================
# DELETE SUPPLIER (ADMIN)
# =========================
@router.get("/delete/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur introuvable")

    db.delete(supplier)
    db.commit()

    return RedirectResponse("/suppliers/page", status_code=303)


# =========================
# UPLOAD INVOICE (ADMIN)
# =========================
@router.post("/upload-invoice/{supplier_id}")
def upload_invoice(
    supplier_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):

    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur introuvable")

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seulement PDF autorisé")

    file_location = f"app/uploads/invoices/{file.filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_invoice = SupplierInvoice(
        supplier_id=supplier_id,
        filename=file.filename,
        file_path=file_location
    )

    db.add(new_invoice)
    db.commit()

    return RedirectResponse(f"/suppliers-edit/{supplier_id}", status_code=303)

@router.post("/upload-invoice/{supplier_id}")
def upload_invoice(
    supplier_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur introuvable")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seulement PDF autorisé")

    # 🔹 Création dossier sécurisé
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR = os.path.join(BASE_DIR, "app", "uploads", "invoices")
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 🔹 Nom unique pour éviter conflits
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    file_location = os.path.join(UPLOAD_DIR, unique_name)

    # 🔹 Sauvegarde fichier
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 🔹 Enregistrement en base
    new_invoice = SupplierInvoice(
        supplier_id=supplier_id,
        filename=file.filename,
        file_path=file_location
    )

    db.add(new_invoice)
    db.commit()

    return RedirectResponse(f"/suppliers-edit/{supplier_id}", status_code=303)

# =========================
# download invoice
# =========================


@router.get("/invoice/download/{invoice_id}")
def download_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    invoice = db.query(SupplierInvoice).filter(SupplierInvoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    if not os.path.exists(invoice.file_path):
        raise HTTPException(status_code=404, detail="Fichier introuvable sur le serveur")

    return FileResponse(
        path=invoice.file_path,
        filename=invoice.filename,
        media_type="application/pdf"
    )
# =========================
# DELETE INVOICE (ADMIN)
# =========================

@router.get("/invoice/delete/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    invoice = db.query(SupplierInvoice).filter(SupplierInvoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    supplier_id = invoice.supplier_id

    # 🔹 Supprime fichier seulement s’il existe
    if os.path.exists(invoice.file_path):
        os.remove(invoice.file_path)

    db.delete(invoice)
    db.commit()

    return RedirectResponse(f"/suppliers-edit/{supplier_id}", status_code=303)

from fastapi import Query
from sqlalchemy import or_

@router.get("/page")
def suppliers_page(
    request: Request,
    search: str = Query(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    query = db.query(Supplier)

    if search:
        query = query.filter(
            or_(
                Supplier.name.ilike(f"%{search}%"),
                Supplier.phone.ilike(f"%{search}%"),
                Supplier.email.ilike(f"%{search}%")
            )
        )

    suppliers = query.all()

    return templates.TemplateResponse(
        "suppliers.html",
        {
            "request": request,
            "suppliers": suppliers,
            "search": search,
            "user": user
        }
    )

@router.get("/create")
def supplier_create_page(
    request: Request,
    user = Depends(require_role("admin"))
):
    return templates.TemplateResponse(
        "supplier_create.html",
        {
            "request": request,
            "user": user
        }
    )

@router.get("/edit/{supplier_id}")
def supplier_edit_page(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur introuvable")

    return templates.TemplateResponse(
        "supplier_edit.html",
        {
            "request": request,
            "supplier": supplier,
            "user": user
        }
    )