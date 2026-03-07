from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.security import hash_password
from app.utils.dependencies import require_role, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])
templates = Jinja2Templates(directory="templates")

# admin-only checks use require_role decorator


# ---------------------------
# 📋 Liste des utilisateurs
# ---------------------------
@router.get("/page")
def user_list_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    users = db.query(User).order_by(User.id.desc()).all()

    return templates.TemplateResponse(
        "user_list.html",
        {
            "request": request,
            "users": users,
            "user": current_user
        }
    )


# ---------------------------
# 🔁 Modifier rôle
# ---------------------------
@router.post("/change-role/{user_id}")
def change_role(
    user_id: int,
    new_role: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    allowed_roles = ["admin", "caissier", "pharmacien"]

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Impossible de modifier son propre rôle")

    if new_role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Rôle invalide")

    user.role = new_role
    db.commit()

    return RedirectResponse("/users/page", status_code=303)


# ---------------------------
# Status Activer / Désactiver
# ---------------------------
@router.post("/toggle-status/{user_id}")
def toggle_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Impossible de se désactiver soi-même")

    user.is_active = not user.is_active
    db.commit()

    return RedirectResponse("/users/page", status_code=303)


# ---------------------------
#  Supprimer utilisateur
# ---------------------------
@router.post("/delete/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    from app.models.sale import Sale  # Import here to avoid circular import

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        users = db.query(User).order_by(User.id.desc()).all()
        return templates.TemplateResponse(
            "user_list.html",
            {
                "request": request,
                "users": users,
                "user": current_user,
                "error": "Utilisateur introuvable"
            }
        )

    if user.id == current_user.id:
        users = db.query(User).order_by(User.id.desc()).all()
        return templates.TemplateResponse(
            "user_list.html",
            {
                "request": request,
                "users": users,
                "user": current_user,
                "error": "Impossible de se supprimer soi-même"
            }
        )

    # Check if user has sales
    sales_count = db.query(Sale).filter(Sale.user_id == user_id).count()
    if sales_count > 0:
        users = db.query(User).order_by(User.id.desc()).all()
        return templates.TemplateResponse(
            "user_list.html",
            {
                "request": request,
                "users": users,
                "user": current_user,
                "error": f"Impossible de supprimer cet utilisateur car il a {sales_count} vente(s) associée(s). Désactivez-le plutôt."
            }
        )

    db.delete(user)
    db.commit()

    return RedirectResponse("/users/page", status_code=303)
    # ---------------------------
# 👤 Mon Profil
# ---------------------------
@router.get("/profile")
def my_profile(
    request: Request,
    current_user: User = Depends(get_current_user)):
    success = request.query_params.get("success")

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": current_user,
            "success": success
        }
    )

@router.post("/profile/update")
def update_profile(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(None),
    confirm_password: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):


    user = db.query(User).filter(User.id == current_user.id).first()

    # Vérifier username déjà utilisé
    existing_username = db.query(User).filter(
        User.username == username,
        User.id != current_user.id
    ).first()

    if existing_username:
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": current_user,
                "error": "Ce nom d'utilisateur est déjà utilisé"
            }
        )

    # Vérifier email déjà utilisé
    existing_email = db.query(User).filter(
        User.email == email,
        User.id != current_user.id
    ).first()

    if existing_email:
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": current_user,
                "error": "Cet email est déjà utilisé"
            }
        )

    user.username = username
    user.email = email

    # Vérification mot de passe
    if password:
        if password != confirm_password:
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "user": current_user,
                    "error": "Les mots de passe ne correspondent pas"
                }
            )

        user.password_hash = hash_password(password)

    db.commit()
    db.refresh(user)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "success": True
        }
    )