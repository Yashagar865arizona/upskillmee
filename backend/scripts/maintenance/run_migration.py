"""
Script to run the migration to add user_id column to projects table
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
env_file = backend_dir / '.env.development'
if env_file.exists():
    load_dotenv(env_file)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to add user_id column to projects table"""
    try:
        # Check if the migration file exists
        migration_file = os.path.join('app', 'database', 'migrations', 'add_user_id_to_projects.py')
        if not os.path.exists(migration_file):
            logger.error(f"Migration file {migration_file} not found")
            return False

        # Create a temporary migration script
        with open('temp_migration.py', 'w') as f:
            f.write("""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment or use default
database_url = os.environ.get('DATABASE_URL', 'postgresql://localhost/ponder')

# Create engine and session
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Add user_id column to projects table if it doesn't exist
    # First check if the column exists
    column_exists = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='projects' AND column_name='user_id'")).fetchone()
    if not column_exists:
        # Add the column if it doesn't exist
        session.execute(text('ALTER TABLE projects ADD COLUMN user_id VARCHAR'))
        print("Added user_id column to projects table")
    else:
        print("user_id column already exists in projects table")

    # Check if the constraint exists
    constraint_exists = session.execute(text("SELECT constraint_name FROM information_schema.table_constraints WHERE table_name='projects' AND constraint_name='fk_projects_user_id_users'")).fetchone()
    if not constraint_exists:
        # Add the constraint if it doesn't exist
        session.execute(text('ALTER TABLE projects ADD CONSTRAINT fk_projects_user_id_users FOREIGN KEY (user_id) REFERENCES users(id)'))
        print("Added foreign key constraint to projects table")
    else:
        print("Foreign key constraint already exists in projects table")
    session.commit()
    print("Migration successful: Added user_id column to projects table")
except Exception as e:
    session.rollback()
    print(f"Migration failed: {str(e)}")
finally:
    session.close()
""")

        # Run the temporary migration script
        logger.info("Running migration...")
        result = subprocess.run([sys.executable, 'temp_migration.py'],
                               capture_output=True, text=True)

        # Log the output
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.error(result.stderr)

        # Clean up
        if os.path.exists('temp_migration.py'):
            os.remove('temp_migration.py')

        return "successful" in result.stdout

    except Exception as e:
        logger.error(f"Error running migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed")
