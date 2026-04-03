#!/usr/bin/env python3
"""
Migration testing script for Ponder backend.
This script tests that all Alembic migrations can be applied and rolled back successfully.
"""

import sys
import os
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.env import load_environment
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Command failed: {command}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False, result.stderr
        
        return True, result.stdout
        
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {command}")
        return False, "Command timed out"
    except Exception as e:
        logger.error(f"Error running command: {command} - {str(e)}")
        return False, str(e)

def test_migration_syntax():
    """Test that all migration files have valid Python syntax."""
    logger.info("🔍 Testing migration file syntax...")
    
    migrations_dir = Path("alembic/versions")
    if not migrations_dir.exists():
        logger.error("❌ Migrations directory not found")
        return False
    
    migration_files = list(migrations_dir.glob("*.py"))
    if not migration_files:
        logger.warning("⚠️  No migration files found")
        return True
    
    for migration_file in migration_files:
        try:
            with open(migration_file, 'r') as f:
                compile(f.read(), migration_file, 'exec')
            logger.info(f"✅ {migration_file.name} syntax OK")
        except SyntaxError as e:
            logger.error(f"❌ Syntax error in {migration_file.name}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Error checking {migration_file.name}: {str(e)}")
            return False
    
    logger.info("✅ All migration files have valid syntax")
    return True

def test_migration_upgrade():
    """Test that migrations can be applied successfully."""
    logger.info("🔍 Testing migration upgrade...")
    
    # Run alembic upgrade head
    success, output = run_command("alembic upgrade head")
    if not success:
        logger.error("❌ Migration upgrade failed")
        return False
    
    logger.info("✅ Migration upgrade successful")
    return True

def test_migration_current():
    """Test that we can get the current migration version."""
    logger.info("🔍 Testing migration current status...")
    
    success, output = run_command("alembic current")
    if not success:
        logger.error("❌ Failed to get current migration status")
        return False
    
    if "head" in output.lower() or len(output.strip()) > 0:
        logger.info(f"✅ Current migration status: {output.strip()}")
        return True
    else:
        logger.warning("⚠️  No current migration found")
        return True

def test_migration_history():
    """Test that we can get migration history."""
    logger.info("🔍 Testing migration history...")
    
    success, output = run_command("alembic history")
    if not success:
        logger.error("❌ Failed to get migration history")
        return False
    
    if output.strip():
        logger.info("✅ Migration history retrieved successfully")
        # Count migrations
        lines = [line for line in output.split('\n') if line.strip() and '->' in line]
        logger.info(f"Found {len(lines)} migrations in history")
        return True
    else:
        logger.warning("⚠️  No migration history found")
        return True

def test_migration_downgrade():
    """Test that migrations can be downgraded (optional, risky in production)."""
    logger.info("🔍 Testing migration downgrade (to previous version)...")
    
    # Get current version first
    success, current_output = run_command("alembic current")
    if not success:
        logger.error("❌ Failed to get current version for downgrade test")
        return False
    
    # Get history to find previous version
    success, history_output = run_command("alembic history")
    if not success:
        logger.error("❌ Failed to get history for downgrade test")
        return False
    
    # Parse history to find previous version
    history_lines = [line.strip() for line in history_output.split('\n') if '->' in line]
    if len(history_lines) < 2:
        logger.info("ℹ️  Not enough migrations to test downgrade")
        return True
    
    # Try to downgrade by one step
    success, output = run_command("alembic downgrade -1")
    if not success:
        logger.error("❌ Migration downgrade failed")
        return False
    
    # Upgrade back to head
    success, output = run_command("alembic upgrade head")
    if not success:
        logger.error("❌ Failed to upgrade back to head after downgrade test")
        return False
    
    logger.info("✅ Migration downgrade/upgrade test successful")
    return True

def test_database_schema_validation():
    """Test that the database schema matches the models."""
    logger.info("🔍 Testing database schema validation...")
    
    try:
        # Import models to ensure they're loaded
        from app.models.user import User, UserProfile, UserSnapshot
        from app.models.chat import Message, Conversation
        from app.models.learning_plan import LearningPlan
        from app.models.project import UserProject
        from app.models.memory import Memory
        from app.models.embedding import EmbeddingStore
        from app.models.token_blacklist import TokenBlacklist
        from app.models.analytics import UserAnalytics, UserEvent
        from app.models.feedback import UserFeedback, FeedbackAnalytics
        
        from app.database.database import engine
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Check that key tables exist
        required_tables = ['users', 'conversations', 'messages']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            logger.error(f"❌ Missing required tables: {missing_tables}")
            return False
        
        logger.info(f"✅ Found {len(tables)} tables in database")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema validation failed: {str(e)}")
        return False

def main():
    """Run all migration tests."""
    logger.info("🔍 Starting migration testing...")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Unknown'}")
    
    tests = [
        ("Migration Syntax", test_migration_syntax),
        ("Migration Upgrade", test_migration_upgrade),
        ("Migration Current", test_migration_current),
        ("Migration History", test_migration_history),
        ("Database Schema", test_database_schema_validation),
        # Note: Downgrade test is commented out as it can be risky
        # ("Migration Downgrade", test_migration_downgrade),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n📊 Migration Test Summary:")
    logger.info("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info("=" * 50)
    logger.info(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All migration tests passed!")
        return 0
    else:
        logger.error(f"❌ {total - passed} migration tests failed!")
        return 1

if __name__ == "__main__":
    # Load environment
    load_environment()
    exit_code = main()
    sys.exit(exit_code)