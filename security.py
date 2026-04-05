from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
import os
import hashlib
import base64
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # ✅ keep, once
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")   # ✅ keep


def _prepare_password(password: str) -> str:
    """
    SHA-256 hash the password and base64-encode it before passing to bcrypt.
    This ensures the input is always 44 chars — well within bcrypt's 72-byte limit —
    while preserving full password entropy for passwords of any length.
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()  # 32 raw bytes
    return base64.b64encode(digest).decode("utf-8")             # 44 ASCII chars


def hash_password(password: str) -> str:
    return pwd_context.hash(_prepare_password(password))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_prepare_password(plain), hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


# ─── Role Guards ──────────────────────────────────────────────────────────────

def require_roles(*roles: models.RoleEnum):
    def checker(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {[r.value for r in roles]}"
            )
        return current_user
    return checker


require_admin            = require_roles(models.RoleEnum.admin)
require_analyst_or_admin = require_roles(models.RoleEnum.analyst, models.RoleEnum.admin)
require_any_role         = require_roles(models.RoleEnum.viewer, models.RoleEnum.analyst, models.RoleEnum.admin)