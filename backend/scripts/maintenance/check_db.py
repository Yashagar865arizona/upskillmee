"""
Script to check database contents.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables from the correct location
env_file = backend_dir / '.env.development'
if env_file.exists():
    load_dotenv(env_file)
else:
    print(f"Warning: Environment file {env_file} not found")

# Get database URL
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL not found in environment variables")
    print("Please ensure .env.development file exists with DATABASE_URL")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

def check_tables():
    """Check contents of chat-related tables."""
    tables = ['messages', 'conversations', 'chat_sessions']
    
    with engine.connect() as conn:
        for table in tables:
            try:
                result = conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
                count = result.scalar()
                print(f"{table}: {count} records")
                
                # If there's data, show a sample
                if count > 0:
                    sample = conn.execute(text(f'SELECT * FROM {table} LIMIT 1'))
                    print(f"Sample record: {dict(sample.first())}")
                    print("-" * 50)
            except Exception as e:
                print(f"Error checking {table}: {str(e)}")

if __name__ == "__main__":
    print(f"Checking database: {DATABASE_URL}")
    check_tables() 