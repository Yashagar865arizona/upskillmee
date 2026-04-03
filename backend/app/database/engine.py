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

# NOTE: Schema is managed by Alembic migrations (alembic upgrade head).
# create_all is intentionally NOT called here so that importing this module
# does not require a live database connection (needed for unit tests).
