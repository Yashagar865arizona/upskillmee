"""
Token blacklist model for handling logout and token invalidation.
"""

from sqlalchemy import Column, String, DateTime, func
from ..database.base import Base
from .base_model import BaseModel
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
import uuid

class TokenBlacklist(BaseModel, Base):
    __tablename__ = "token_blacklist"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    token_jti = Column(String, unique=True, nullable=False, index=True)  # JWT ID
    user_id = Column(String, nullable=False, index=True)
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)  # When the token would naturally expire