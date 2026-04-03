"""
Script to clear chat data in the development environment.
This script safely deletes all chat-related data from the database.
"""

import psycopg2
import logging
from typing import List, Optional
from app.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tables to clear in order (respecting foreign key constraints)
CHAT_TABLES = [
    'messages',
    'conversations',
    'chat_sessions',
    'embedding_store'  # For vector embeddings of messages
]

def get_confirmation() -> bool:
    """Get user confirmation before proceeding with deletion."""
    print("\nWARNING: This will permanently delete all chat data from the database.")
    print("This action cannot be undone.")
    print("\nTables to be cleared:")
    for table in CHAT_TABLES:
        print(f"- {table}")
    
    response = input("\nAre you sure you want to proceed? (yes/no): ").lower()
    return response == 'yes'

def clear_chat_data(tables: Optional[List[str]] = None) -> None:
    """
    Clear chat data from specified tables or all chat tables.
    
    Args:
        tables: Optional list of specific tables to clear. If None, clears all chat tables.
    """
    # Use provided tables or default to all chat tables
    tables_to_clear = tables or CHAT_TABLES
    
    # Get confirmation
    if not get_confirmation():
        print("Operation cancelled.")
        return

    # Connect to the database
    logger.info(f"Connecting to database: {settings.DATABASE_URL}")
    conn = psycopg2.connect(settings.DATABASE_URL)
    cursor = conn.cursor()

    # Begin transaction
    conn.autocommit = False

    try:
        total_deleted = 0
        
        # Delete data from each table
        for table in tables_to_clear:
            try:
                # Check if table exists
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    );
                """)
                if not cursor.fetchone()[0]:
                    logger.warning(f"Table '{table}' does not exist, skipping...")
                    continue
                
                # Delete data from table
                cursor.execute(f'DELETE FROM {table}')
                count = cursor.rowcount
                total_deleted += count
                logger.info(f'Deleted {count} records from {table}')
                
            except Exception as e:
                logger.error(f"Error clearing table {table}: {str(e)}")
                raise
        
        # Commit the transaction
        conn.commit()
        logger.info(f'Successfully cleared chat data. Total records deleted: {total_deleted}')
        
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        logger.error(f'Error clearing chat data: {str(e)}')
        raise
    finally:
        # Close cursor and connection
        cursor.close()
        conn.close()

if __name__ == "__main__":
    try:
        clear_chat_data()
    except Exception as e:
        logger.error(f"Failed to clear chat data: {str(e)}")
        exit(1) 