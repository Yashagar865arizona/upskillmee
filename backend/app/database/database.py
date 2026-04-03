"""
Database connection and session management with connection pooling and retry logic.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from ..config import settings
import logging
from contextlib import contextmanager
from typing import Generator
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import traceback

logger = logging.getLogger(__name__)

# Database URL from settings
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Optimized database engine configuration with improved connection pooling
engine_config = {
    "pool_size": 5,  # Reduced permanent connections for better resource usage
    "max_overflow": 10,  # Reduced overflow connections
    "pool_timeout": 20,  # Reduced timeout for faster failure detection
    "pool_recycle": 1800,  # Recycle connections every 30 minutes
    "pool_pre_ping": True,  # Enable connection health checks
    "pool_reset_on_return": "commit",  # Reset connections on return
    "echo": settings.ENVIRONMENT == "development",  # Log SQL in development
    "echo_pool": settings.ENVIRONMENT == "development",  # Log pool events in development
}

# Add PostgreSQL-specific optimizations
if "postgresql" in SQLALCHEMY_DATABASE_URL:
    engine_config.update({
        "connect_args": {
            "connect_timeout": 10,
            "application_name": "ponder_backend",
        }
    })

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_config)

# Create async engine only if using async driver
async_engine = None
if "postgresql+asyncpg://" in SQLALCHEMY_DATABASE_URL:
    async_engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )

# Refresh metadata to ensure all columns are recognized
from sqlalchemy import MetaData
metadata = MetaData()
metadata.reflect(bind=engine)
logger.info(f"Refreshed database metadata with tables: {metadata.tables.keys()}")

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = None
if async_engine:
    AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Create base class for declarative models
class Base(DeclarativeBase):
    pass

@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database transaction error: {str(e)}")
        logger.debug(f"Transaction traceback: {''.join(traceback.format_tb(e.__traceback__))}")
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error in database transaction: {str(e)}")
        logger.error(f"Error traceback: {''.join(traceback.format_tb(e.__traceback__))}")
        raise
    finally:
        session.close()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def get_db():
    """Get database session with retry logic."""
    db = None
    try:
        db = SessionLocal()
        logger.debug("Database session created successfully")
        yield db
    except OperationalError as e:
        logger.error(f"Database connection error: {str(e)}")
        logger.debug(f"Connection traceback: {''.join(traceback.format_tb(e.__traceback__))}")
        raise
    except Exception as e:
        logger.error(f"Unexpected database error: {str(e)}")
        logger.error(f"Error traceback: {''.join(traceback.format_tb(e.__traceback__))}")
        raise
    finally:
        if db is not None:
            db.close()
            logger.debug("Database session closed")

async def get_async_db():
    """Get async database session with retry logic."""
    if not AsyncSessionLocal:
        raise RuntimeError("Async database not configured")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Error in async database session: {str(e)}")
            raise

# Initialize query performance monitoring
try:
    from ..services.query_performance_service import query_performance_monitor
    
    # Set up automatic query monitoring
    query_performance_monitor.setup_sqlalchemy_monitoring(engine)
    logger.info("Query performance monitoring enabled")
except ImportError:
    logger.warning("Query performance monitoring not available")

# Connection pool event listeners
@event.listens_for(engine, 'connect')
def connect(dbapi_connection, connection_record):
    logger.debug("New database connection established")

@event.listens_for(engine, 'checkout')
def checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug("Database connection checked out from pool")

@event.listens_for(engine, 'checkin')
def checkin(dbapi_connection, connection_record):
    logger.debug("Database connection returned to pool")