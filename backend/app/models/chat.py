"""
Location: ponder/backend/app/models/chat.py

This module defines the database models for the chat functionality using SQLAlchemy ORM.
It includes:
- Conversation: Represents a chat conversation between a user and the AI
- Message: Represents individual messages within a conversation, including their vector embeddings
"""

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
    JSON,
)
from sqlalchemy.orm import relationship, validates
from datetime import datetime
from ..database.base import Base
from .base_model import BaseModel
import json
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Conversation(BaseModel, Base):
    __tablename__ = "conversations"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    title = Column(String(255))
    status = Column(String(50), default='active')
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    user = relationship("User", back_populates="conversations")

    __table_args__ = (
        Index('idx_conversation_user_created', user_id, created_at),
        CheckConstraint(status.in_(['active', 'archived', 'deleted']), name='valid_status'),
    )

    @validates('title')
    def validate_title(self, key, value):
        if value and len(value) > 255:
            return value[:255]
        return value

class Message(BaseModel, Base):
    __tablename__ = "messages"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)
    message_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages")

    __table_args__ = (
        Index('idx_message_user_created', user_id, created_at),
        Index('idx_message_conversation', conversation_id),
    )

    @validates('content')
    def validate_content(self, key, value):
        if not value:
            raise ValueError("Message content cannot be empty")
        if len(value) > 10000:  # Limit message length to 10K characters
            raise ValueError("Message content too long")
        return value

    @validates('message_metadata')
    def validate_metadata(self, key, value):
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return {}
