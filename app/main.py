from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.database import engine, Base
from app.models.product import Product
from app.models.sale import Sale
from app.models.supplier import Supplier
from app.models.user import User
from app.routes import auth,  suppliers, products, sales, stock, users
from app.utils.dependencies import get_current_user, require_role
from sqlalchemy.orm import Session
from app.database import get_db
from datetime import date
from app.models import supplier_invoice
from app.routes import dashboard
import os

UPLOAD_DIR = "app/uploads/invoices"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(auth.router)
app.include_router(suppliers.router)
app.include_router(products.router)
app.include_router(stock.router)
app.include_router(sales.router)
app.include_router(dashboard.router)
app.include_router(users.router)


# Create tables
Base.metadata.create_all(bind=engine)

# ----------------------------------------------------Routes pour les pages HTML-----------------------------------------------------------------

# ========================================
# PAGE D'ACCUEIL (REDIRECT VERS LOGIN)
# ========================================
@app.get("/")
def redirect_to_login():
    return RedirectResponse("/login")
@app.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "role": current_user.role
    }

#===================ROUTE DE TEST ADMIN ONLY============================================================================
@app.get("/admin-only")
def admin_route(user: User = Depends(require_role("admin"))):
    return {"message": "Welcome Admin"}

#=====================ROUTE DE LOGIN ===================================================================================
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

#====================ROUTE DE SIGNUP(inscription) =======================================================================
@app.get("/signup")
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})
