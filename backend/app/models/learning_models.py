"""
Learning models for tracking user learning progress and sessions.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
from ..database.base import Base
from .base_model import BaseModel
from sqlalchemy.dialects.postgresql import UUID
import uuid

class LearningProgress(BaseModel, Base):
    __tablename__ = "learning_progress"

    user_id = Column(String, ForeignKey("users.id"))
    topic = Column(String)
    progress = Column(Float)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="learning_progress_items")

class LearningSession(BaseModel, Base):
    __tablename__ = "learning_sessions"

    user_id = Column(String, ForeignKey("users.id"))
    start_time = Column(DateTime(timezone=True))
    duration = Column(Float)  # in minutes
    topic = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="learning_sessions")
