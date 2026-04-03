"""
Database engine configuration.
"""

import os
import logging
from sqlalchemy import create_engine
from ..config import settings
from .base import Base

logger = logging.getLogger(__name__)

# Database URL configuration
DATABASE_URL = settings.DATABASE_URL

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_size=5,  # Default pool size
    max_overflow=10  # Default max overflow
)

# Create all tables
Base.metadata.create_all(bind=engine)

# Test database connection
try:
    with engine.connect() as conn:
        logger.info("Successfully connected to the database")
except Exception as e:
    logger.error(f"Database connection failed: {str(e)}")
    raise
