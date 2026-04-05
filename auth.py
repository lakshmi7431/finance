from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import models, schemas
from app.security import hash_password, verify_password, create_access_token, pwd_context

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):

    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    is_first_user = db.query(models.User).count() == 0
    role = models.RoleEnum.admin if is_first_user else user_data.role

    user = models.User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=role
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _authenticate_user(email: str, password: str, db: Session) -> models.User:
    """Shared auth logic used by both login endpoints."""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Contact an admin."
        )
    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Login with email + password as JSON. Used by your app/API clients."""
    user = _authenticate_user(credentials.email, credentials.password, db)
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"access_token": token}


@router.post("/token", response_model=schemas.TokenResponse)
def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 form-data login — for Swagger UI's Authorize dialog only.
    Enter your email in the 'username' field and your password in 'password'.
    """
    user = _authenticate_user(form_data.username, form_data.password, db)
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"access_token": token}