"""
Base model with common fields for all models.
"""

from sqlalchemy import Column, String, DateTime, func, Integer
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from uuid import uuid4
from ..database.base import Base

class BaseModel:
    """Abstract base class for all models"""
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() + 's'
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
