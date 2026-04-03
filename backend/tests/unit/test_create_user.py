"""
Test utility for creating test users.
"""

from sqlalchemy.orm import Session
from app.models.user import User
from app.database import SessionLocal

def create_test_user():
    """Create a test user in the database."""
    db = SessionLocal()
    try:
        user = User(id="test_user")
        db.add(user)
        db.commit()
        print("Test user created successfully")
    except Exception as e:
        print(f"Error creating test user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()