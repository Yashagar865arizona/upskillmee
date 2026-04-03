"""
Memory model for storing and retrieving memories.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, JSON
from ..database import Base

class MemoryType(str, Enum):
    """Types of memories that can be stored."""
    CONVERSATION = "conversation"
    LEARNING = "learning"
    REFLECTION = "reflection"
    GOAL = "goal"
    TASK = "task"

class Memory(Base):
    """Memory model for storing and retrieving memories."""

    __tablename__ = "memories"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    content = Column(String, nullable=False)
    memory_type = Column(String, nullable=False)
    meta_data = Column(JSON, nullable=False, default={})
    embedding = Column(JSON, nullable=True)
    user_id = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(
        self,
        content: str,
        memory_type: str,
        meta_data: Dict[str, Any] = None,
        embedding: List[float] = None,
        user_id: str = None
    ):
        """Initialize a new memory."""
        self.id = str(uuid4())
        self.content = content
        self.memory_type = memory_type
        self.meta_data = meta_data or {}
        self.embedding = embedding
        self.user_id = user_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "meta_data": self.meta_data,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        } 