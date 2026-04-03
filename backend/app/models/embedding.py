"""
Embedding model for storing vector embeddings in PostgreSQL.
This allows semantic search and retrieval of content.
"""

import json
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, JSON
from sqlalchemy.sql import func
from uuid import uuid4
from datetime import datetime
import struct
import logging

from ..database.database import Base

logger = logging.getLogger(__name__)

class Embedding(Base):
    """SQLAlchemy model for text embeddings"""
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    embedding_vector = Column(Text)
    meta_data = Column(JSON, default={})
    user_id = Column(String)
    conversation_id = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __init__(self, **kwargs):
        """Initialize the embedding with meta_data and vector"""
        # Handle the meta_data correctly - store in meta_data field regardless of input name
        if "metadata" in kwargs and "meta_data" not in kwargs:
            kwargs["meta_data"] = kwargs.pop("metadata")
        elif "meta_data" not in kwargs:
            kwargs["meta_data"] = {}
            
        # Ensure embedding_vector is stored as a string
        if "embedding_vector" in kwargs and kwargs["embedding_vector"]:
            if not isinstance(kwargs["embedding_vector"], str):
                kwargs["embedding_vector"] = json.dumps(kwargs["embedding_vector"])
        
        super().__init__(**kwargs)
    
    def __repr__(self):
        """String representation of the embedding"""
        return f"<Embedding id={self.id} content_preview='{self.content[:30]}...'>" 