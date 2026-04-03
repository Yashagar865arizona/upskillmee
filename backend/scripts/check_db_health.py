#!/usr/bin/env python3
"""
Database health check script for Ponder backend.
This script verifies database connectivity, migration status, and basic functionality.
"""

import sys
import os
import logging
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.env import load_environment
from app.database.database import engine, SessionLocal
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Test basic database connectivity."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        return False

def check_database_tables():
    """Check if required tables exist."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            'users', 'conversations', 'messages', 'user_snapshots',
            'user_profiles', 'learning_plans', 'user_projects',
            'memory', 'embedding_store', 'token_blacklist',
            'user_analytics', 'user_events', 'user_feedback'
        ]
        
        missing_tables = []
        for table in required_tables:
            if table in tables:
                logger.info(f"✅ Table '{table}' exists")
            else:
                missing_tables.append(table)
                logger.warning(f"⚠️  Table '{table}' missing")
        
        if missing_tables:
            logger.error(f"❌ Missing tables: {missing_tables}")
            return False
        
        logger.info("✅ All required tables exist")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking tables: {str(e)}")
        return False

def check_database_indexes():
    """Check if important indexes exist."""
    try:
        with engine.connect() as conn:
            # Check for important indexes
            index_queries = [
                "SELECT indexname FROM pg_indexes WHERE tablename = 'messages' AND indexname LIKE '%conversation_id%'",
                "SELECT indexname FROM pg_indexes WHERE tablename = 'messages' AND indexname LIKE '%user_id%'",
                "SELECT indexname FROM pg_indexes WHERE tablename = 'conversations' AND indexname LIKE '%user_id%'",
            ]
            
            for query in index_queries:
                result = conn.execute(text(query))
                indexes = result.fetchall()
                if indexes:
                    logger.info(f"✅ Found indexes: {[idx[0] for idx in indexes]}")
                else:
                    logger.warning(f"⚠️  No indexes found for query: {query}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking indexes: {str(e)}")
        return False

def check_database_extensions():
    """Check if required PostgreSQL extensions are installed."""
    try:
        with engine.connect() as conn:
            # Check for vector extension (if using pgvector)
            result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
            if result.fetchone():
                logger.info("✅ Vector extension is installed")
            else:
                logger.info("ℹ️  Vector extension not installed (optional)")
            
            # Check for uuid extension
            result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'uuid-ossp'"))
            if result.fetchone():
                logger.info("✅ UUID extension is installed")
            else:
                logger.warning("⚠️  UUID extension not installed")
            
            # Check for pg_stat_statements
            result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'pg_stat_statements'"))
            if result.fetchone():
                logger.info("✅ pg_stat_statements extension is installed")
            else:
                logger.warning("⚠️  pg_stat_statements extension not installed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking extensions: {str(e)}")
        return False

def check_migration_status():
    """Check Alembic migration status."""
    try:
        with engine.connect() as conn:
            # Check if alembic_version table exists
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"
            ))
            
            if result.fetchone()[0]:
                # Get current migration version
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.fetchone()
                if version:
                    logger.info(f"✅ Current migration version: {version[0]}")
                else:
                    logger.warning("⚠️  No migration version found")
            else:
                logger.warning("⚠️  Alembic version table not found - migrations may not have been run")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking migration status: {str(e)}")
        return False

def check_connection_pool():
    """Test connection pool functionality."""
    try:
        # Test multiple concurrent connections
        sessions = []
        for i in range(5):
            session = SessionLocal()
            result = session.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
            sessions.append(session)
        
        # Close all sessions
        for session in sessions:
            session.close()
        
        logger.info("✅ Connection pool test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection pool test failed: {str(e)}")
        return False

def main():
    """Run all database health checks."""
    logger.info("🔍 Starting database health check...")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Unknown'}")
    
    checks = [
        ("Database Connection", check_database_connection),
        ("Database Tables", check_database_tables),
        ("Database Indexes", check_database_indexes),
        ("Database Extensions", check_database_extensions),
        ("Migration Status", check_migration_status),
        ("Connection Pool", check_connection_pool),
    ]
    
    results = []
    for check_name, check_func in checks:
        logger.info(f"\n🔍 Running {check_name} check...")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"❌ {check_name} check failed with exception: {str(e)}")
            results.append((check_name, False))
    
    # Summary
    logger.info("\n📊 Health Check Summary:")
    logger.info("=" * 50)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{check_name}: {status}")
        if result:
            passed += 1
    
    logger.info("=" * 50)
    logger.info(f"Overall: {passed}/{total} checks passed")
    
    if passed == total:
        logger.info("🎉 All database health checks passed!")
        return 0
    else:
        logger.error(f"❌ {total - passed} health checks failed!")
        return 1

if __name__ == "__main__":
    # Load environment
    load_environment()
    exit_code = main()
    sys.exit(exit_code)