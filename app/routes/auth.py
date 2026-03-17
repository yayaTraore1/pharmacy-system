from fastapi import APIRouter, Depends, HTTPException, status, Form, Response, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.security import hash_password, verify_password, create_access_token
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
import secrets
from app.utils.mailer import send_reset_password_email


# simple in‑memory rate limiter keyed by username+IP
login_attempts: dict[str, list[datetime]] = {}

router = APIRouter(prefix="/auth", tags=["Authentication"])

from fastapi.templating import Jinja2Templates
from fastapi import Request

templates = Jinja2Templates(directory="templates")

# @router.post("/signup")
# def signup(
#     request: Request,
#     username: str = Form(...),
#     email: str = Form(...),
#     password: str = Form(...),
#     role: str = Form("pharmacien"),
#     db: Session = Depends(get_db)
# ):
#     errors = []
#     try:
#         # Validate with Pydantic
#         user_data = UserCreate(username=username, email=email, password=password, role=role)
#     except Exception as e:
#         errors.append(str(e))
    
#     if not errors:
#         if db.query(User).filter(User.username == user_data.username).first():
#             errors.append("Username already exists")
        
#         if db.query(User).filter(User.email == user_data.email).first():
#             errors.append("Email already exists")
    
#     if errors:
#         return templates.TemplateResponse("signup.html", {"request": request, "errors": errors})
    
#     new_user = User(
#         username=user_data.username,
#         email=user_data.email,
#         password=hash_password(user_data.password),
#         role=user_data.role
#     )

#     try:
#         db.add(new_user)
#         db.commit()
#     except Exception as e:
#         db.rollback()
#         errors.append("Database error: " + str(e))
#         return templates.TemplateResponse("signup.html", {"request": request, "errors": errors})

#     return RedirectResponse(url="/login", status_code=303)

@router.post("/login")
def login(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # rate limiter: 5 attempts per minute per user+IP
    ip = request.client.host
    key = f"{form_data.username}:{ip}"
    now = datetime.utcnow()

    # purge old attempts
    attempts = login_attempts.get(key, [])
    attempts = [t for t in attempts if (now - t).total_seconds() < 60]
    if len(attempts) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait and try again later."
        )
    # record the current try
    attempts.append(now)
    login_attempts[key] = attempts

    db_user = db.query(User).filter(User.username == form_data.username).first()

    if not db_user or not verify_password(form_data.password, db_user.password):
        # invalid credentials count as an attempt (already recorded above)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if db_user.is_active is False:
        raise HTTPException(status_code=403, detail="User account is inactive")

    # reset attempt counter on successful login
    login_attempts.pop(key, None)

    token = create_access_token({
        "sub": db_user.username,
        "role": db_user.role
    })

    redirect = RedirectResponse(url="/dashboard", status_code=303)
    redirect.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        secure=True,
        samesite="lax"
    )

    return redirect

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response

@router.get("/create-password")
def create_password_page(request: Request, token: str):
    return templates.TemplateResponse(
        "create_password.html",
        {"request": request, "token": token}
    )

@router.post("/create-password")
def create_password(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.reset_token == token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Lien invalide")

    if user.reset_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Lien expiré")

    if password != confirm_password:
        return templates.TemplateResponse(
            "create_password.html",
            {"request": request, "token": token, "error": "Les mots de passe ne correspondent pas"}
        )

    user.password = hash_password(password)
    user.reset_token = None
    user.reset_token_expiry = None

    db.commit()

    return RedirectResponse("/login?success=Mot de passe créé", status_code=303)

@router.get("/forgot-password")
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@router.post("/forgot-password")
async def forgot_password(
    email: str = Form(...),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        return RedirectResponse("/login", status_code=303)

    token = secrets.token_urlsafe(32)

    user.reset_token = token
    user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)

    db.commit()

    await send_reset_password_email(email, token)

    return RedirectResponse("/login?success=Email envoyé", status_code=303)

@router.get("/reset-password")
def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse(
        "reset_password.html",
        {
            "request": request,
            "token": token
        }
    )


@router.post("/reset-password")
def reset_password(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.reset_token == token).first()

    if not user:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "token": token, "error": "Lien invalide"}
        )

    if user.reset_token_expiry < datetime.utcnow():
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "token": token, "error": "Lien expiré"}
        )

    if password != confirm_password:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "token": token, "error": "Les mots de passe ne correspondent pas"}
        )

    # changer mot de passe
    user.password = hash_password(password)

    # supprimer token
    user.reset_token = None
    user.reset_token_expiry = None

    db.commit()

    return RedirectResponse(
        "/login?success=Mot de passe réinitialisé",
        status_code=303
    )