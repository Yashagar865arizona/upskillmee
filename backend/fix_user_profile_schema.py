#!/usr/bin/env python3
"""
Fix user profile schema issues by updating column types
"""

import sys
import os
sys.path.append('.')

from sqlalchemy import text
from app.database.database import engine

def fix_user_profile_schema():
    """Fix user profile schema by converting VARCHAR[] to JSON columns"""
    
    print("=== Fixing User Profile Schema ===")
    
    # SQL commands to fix the schema
    fix_commands = [
        # Drop and recreate the languages column as JSON
        "ALTER TABLE user_profiles DROP COLUMN IF EXISTS languages CASCADE;",
        "ALTER TABLE user_profiles ADD COLUMN languages JSON DEFAULT '[]'::JSON;",
        
        # Ensure all JSON columns are properly typed
        "ALTER TABLE user_profiles ALTER COLUMN hobbies TYPE JSON USING hobbies::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN preferred_subjects TYPE JSON USING preferred_subjects::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN work_preferences TYPE JSON USING work_preferences::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN career_interests TYPE JSON USING career_interests::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN long_term_goals TYPE JSON USING long_term_goals::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN technical_skills TYPE JSON USING technical_skills::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN soft_skills TYPE JSON USING soft_skills::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN certifications TYPE JSON USING certifications::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN achievements TYPE JSON USING achievements::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN completed_projects TYPE JSON USING completed_projects::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN current_projects TYPE JSON USING current_projects::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN skill_levels TYPE JSON USING skill_levels::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN personality_traits TYPE JSON USING personality_traits::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN cognitive_strengths TYPE JSON USING cognitive_strengths::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN learning_preferences TYPE JSON USING learning_preferences::JSON;",
        "ALTER TABLE user_profiles ALTER COLUMN preferences TYPE JSON USING preferences::JSON;",
    ]
    
    with engine.connect() as conn:
        for command in fix_commands:
            try:
                print(f"Executing: {command}")
                conn.execute(text(command))
                conn.commit()
                print("✅ Success")
            except Exception as e:
                print(f"⚠️  Warning: {str(e)}")
                # Continue with other commands
                continue
    
    print("=== Schema Fix Complete ===")

if __name__ == "__main__":
    fix_user_profile_schema()