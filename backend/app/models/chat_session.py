"""
Chat session model for tracking user chat sessions.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.base import Base
from .base_model import BaseModel
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class ChatSession(BaseModel, Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    session_start = Column(DateTime(timezone=True), default=datetime.utcnow)
    session_end = Column(DateTime(timezone=True), nullable=True)
    messages = Column(Text, nullable=True)  # Store messages or any session data as JSON or text
    
    # Update relationship to use back_populates instead of backref
    user = relationship("User", back_populates="chat_sessions") 