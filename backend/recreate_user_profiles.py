#!/usr/bin/env python3
"""
Recreate user profiles table with correct schema
"""

import sys
import os
sys.path.append('.')

from sqlalchemy import text
from app.database.database import engine

def recreate_user_profiles_table():
    """Drop and recreate user_profiles table with correct JSON columns"""
    
    print("=== Recreating User Profiles Table ===")
    
    # SQL commands to recreate the table
    commands = [
        # Drop the table
        "DROP TABLE IF EXISTS user_profiles CASCADE;",
        
        # Recreate with correct schema
        """
        CREATE TABLE user_profiles (
            id VARCHAR PRIMARY KEY,
            user_id VARCHAR UNIQUE REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            
            -- Basic Info
            name VARCHAR,
            email VARCHAR,
            
            -- Demographics and Background
            age INTEGER,
            location VARCHAR,
            education_level VARCHAR,
            languages JSON DEFAULT '[]'::JSON,
            learning_style VARCHAR,
            
            -- Interests and Preferences
            hobbies JSON DEFAULT '[]'::JSON,
            preferred_subjects JSON DEFAULT '[]'::JSON,
            work_style VARCHAR,
            work_preferences JSON DEFAULT '[]'::JSON,
            career_interests JSON DEFAULT '[]'::JSON,
            long_term_goals JSON DEFAULT '[]'::JSON,
            
            -- Skills and Competencies
            technical_skills JSON DEFAULT '[]'::JSON,
            soft_skills JSON DEFAULT '[]'::JSON,
            certifications JSON DEFAULT '[]'::JSON,
            achievements JSON DEFAULT '[]'::JSON,
            
            -- Learning Progress
            learning_level VARCHAR DEFAULT 'beginner',
            completed_projects JSON DEFAULT '[]'::JSON,
            current_projects JSON DEFAULT '[]'::JSON,
            skill_levels JSON DEFAULT '{}'::JSON,
            
            -- Personality and Preferences
            personality_traits JSON DEFAULT '{}'::JSON,
            cognitive_strengths JSON DEFAULT '[]'::JSON,
            learning_preferences JSON DEFAULT '{}'::JSON,
            preferences JSON DEFAULT '{}'::JSON
        );
        """
    ]
    
    with engine.connect() as conn:
        for command in commands:
            try:
                print(f"Executing command...")
                conn.execute(text(command))
                conn.commit()
                print("✅ Success")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                conn.rollback()
                return False
    
    print("=== User Profiles Table Recreated Successfully ===")
    return True

if __name__ == "__main__":
    recreate_user_profiles_table()