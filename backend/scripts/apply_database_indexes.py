#!/usr/bin/env python3
"""
Script to apply database indexes for performance optimization.
"""

import sys
import os
import logging

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import engine
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def apply_indexes():
    """Apply database indexes for performance optimization."""
    logger.info("Applying database indexes for performance optimization...")
    
    # Indexes to create (without CONCURRENTLY for compatibility)
    indexes_to_create = [
        "CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);",
        "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at);",
        "CREATE INDEX IF NOT EXISTS idx_user_projects_user_id ON user_projects(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_user_projects_status ON user_projects(status);",
        "CREATE INDEX IF NOT EXISTS idx_learning_plans_user_id ON learning_plans(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);",
        # Additional useful indexes
        "CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);",
        "CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);",
        "CREATE INDEX IF NOT EXISTS idx_learning_plans_status ON learning_plans(status);",
        "CREATE INDEX IF NOT EXISTS idx_user_projects_created_at ON user_projects(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_user_projects_updated_at ON user_projects(updated_at);"
    ]
    
    with engine.connect() as connection:
        for index_sql in indexes_to_create:
            try:
                connection.execute(text(index_sql))
                connection.commit()
                index_name = index_sql.split('idx_')[1].split(' ')[0]
                logger.info(f"Created index: {index_name}")
            except Exception as e:
                logger.warning(f"Could not create index: {e}")
                connection.rollback()
        
        # Update table statistics
        try:
            connection.execute(text("ANALYZE;"))
            connection.commit()
            logger.info("Updated table statistics")
        except Exception as e:
            logger.warning(f"Could not update statistics: {e}")
    
    logger.info("Database index optimization completed")

if __name__ == "__main__":
    apply_indexes()