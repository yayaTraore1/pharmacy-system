from fastapi import APIRouter, Depends, HTTPException, status, Form, Response, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import user
from app.models.user import User
from app.schemas.user import UserCreate
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.security import hash_password, verify_password, create_access_token
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta


# simple in‑memory rate limiter keyed by username+IP
login_attempts: dict[str, list[datetime]] = {}

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup")
def signup(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("caissier"),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=username,
        email=email,
        password=hash_password(password),
        role=role
    )

    db.add(new_user)
    db.commit()

    return RedirectResponse(url="/login", status_code=303)

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