"""
Database initialization script.
Creates all tables if they don't exist and performs initial setup.
"""

import logging
import os
import sys
from sqlalchemy import inspect, text, Column, String, Integer, Text, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to the path so we can import from the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.database.database import engine, Base, SessionLocal
from backend.app.models import embedding, user, chat, learning_models, project
from ..config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize database with required tables"""
    try:
        # Create a session
        db = SessionLocal()
        inspector = inspect(engine)
        
        # Log the existing tables
        existing_tables = inspector.get_table_names()
        logger.info(f"Existing tables: {existing_tables}")
        
        # Check if embeddings table exists
        if "embeddings" not in existing_tables:
            logger.info("Creating embeddings table...")
            try:
                # Create embeddings table with proper schema
                db.execute(text("""
                    CREATE TABLE IF NOT EXISTS embeddings (
                        id SERIAL PRIMARY KEY,
                        content TEXT NOT NULL,
                        embedding_vector TEXT,
                        meta_data JSONB,
                        user_id TEXT,
                        conversation_id TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                db.commit()
                logger.info("Successfully created embeddings table")
            except SQLAlchemyError as e:
                logger.error(f"Error creating embeddings table: {str(e)}")
                db.rollback()
        else:
            logger.info("Embeddings table already exists")
            
        # Verify the tables after initialization
        all_tables = inspector.get_table_names()
        logger.info(f"All tables after initialization: {all_tables}")
        
        # Close the session
        db.close()
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        # Try to close the session if it exists
        try:
            if 'db' in locals():
                db.close()
        except:
            pass

if __name__ == "__main__":
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialization complete")