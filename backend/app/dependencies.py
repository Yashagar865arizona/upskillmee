"""
FastAPI dependencies for authentication and common functionality.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
import logging

from .database import get_db
from .services.auth_service import AuthService
from .models.user import User
from jose import jwt, JWTError
from app.config.settings import settings

logger = logging.getLogger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
SECRET_KEY = settings.JWT_SECRET
ALGORITHM = settings.JWT_ALGORITHM
def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get instance of AuthService with proper configuration"""
    return AuthService(db)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        print("Decoded Payload:", payload)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db.refresh(user)
        return user

    except Exception as e:
        logger.error(f"get_current_user error: {e}")
        raise HTTPException(status_code=401, detail="Authentication error")

def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    print(f"[ADMIN CHECK] email={current_user.email}, is_admin={current_user.is_admin}")
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to get the current authenticated active user."""
    if not getattr(current_user, 'is_active', True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user