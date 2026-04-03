"""
Database session configuration.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Generator, AsyncGenerator, Any

from ..config import settings

# Get database URI from settings
DB_URI = settings.DATABASE_URL

# Create a database engine for synchronous operations
engine = create_engine(
    DB_URI,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

# Create a sessionmaker for standard operations
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Create async engine for WebSocket operations
async_engine = create_async_engine(
    DB_URI.replace('postgresql://', 'postgresql+asyncpg://'),
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

# Create an async sessionmaker - use the proper async_sessionmaker
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=async_engine,
)

def get_db() -> Generator[Session, None, None]:
    """
    Create a new database session for a request.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a new async database session for WebSocket connections.
    
    Yields:
        AsyncSession: Async SQLAlchemy database session
    """
    async with AsyncSessionLocal() as session:
        yield session
