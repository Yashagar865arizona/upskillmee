"""
Location: ponder/backend/app/services/user_service.py

This module implements the user service functionality for the FastAPI backend.

Enhanced user service combining user management and onboarding functionality.
Key features:
- User profile management
- Multi-step onboarding process
- Profile information collection
- Career path guidance
- Learning style assessment
- Notification management
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List, Sequence
from ..models.user import UserProfile, User,Psychometric
from .message_service import MessageService
from ..config import settings
import logging
from datetime import datetime, timezone
import uuid
import traceback
from fastapi import HTTPException
from sqlalchemy import Column
from app.scripts.psychometric_questions import DEFAULT_QUESTIONS


logger = logging.getLogger(__name__)

class OnboardingStep:
    WELCOME = 1
    BASIC_INFO = 2
    CAREER_PATH = 3
    TECHNICAL_BACKGROUND = 4
    LEARNING_STYLE = 5
    GOALS = 6
    PREFERENCES = 7
    COMPLETE = 8

class UserService:
    def __init__(self, db: Session):
        self.db = db

    async def get_user(self, db: Session, user_id: str) -> Dict:
        """Get user data by ID."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        return {
            "id": user.id,
            "name": getattr(user, 'name', ''),
            "status": getattr(user, 'status', 'active'),
            "avatar_url": getattr(user, 'avatar_url', "https://via.placeholder.com/30x30"),
            "profile": {
                "learning_level": getattr(profile, 'learning_level', 'beginner') if profile else "beginner",
                "career_interests": getattr(profile, 'career_interests', []) if profile else [],
                "technical_skills": getattr(profile, 'technical_skills', []) if profile else []
            } if profile else None
        }

    # async def get_notifications(self, db: Session, user_id: str) -> Dict:
    #     """Get user notifications."""
    #     user = db.query(User).filter(User.id == user_id).first()
    #     if not user:
    #         raise HTTPException(status_code=404, detail="User not found")
            
    #     # Get actual notification counts from database
    #     from ..models import Conversation, UserProject
        
    #     # Count recent conversations (learning activities)
    #     learning_count = db.query(Conversation).filter(
    #         Conversation.user_id == str(user_id),
    #         Conversation.status == 'active'
    #     ).count()
        
    #     # Count user projects (progress activities)
    #     progress_count = db.query(UserProject).filter(
    #         UserProject.user_id == str(user_id)
    #     ).count()
        
    #     return {
    #         "learning_count": learning_count,
    #         "progress_count": progress_count
    #     }

    async def handle_onboarding_step(self, db: Session, user_id: str, step: int, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle each step of the onboarding process."""
        try:
            # First check if user exists, if not create one
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                user = User()
                setattr(user, 'id', user_id)
                setattr(user, 'name', data.get('name', 'New User') if data else 'New User')
                setattr(user, 'status', 'active')
                db.add(user)
                db.flush()  # Flush to get the user ID
            
            # Get or create user profile
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                profile = UserProfile()
                setattr(profile, 'id', str(uuid.uuid4()))
                setattr(profile, 'user_id', user_id)
                setattr(profile, 'name', data.get('name', 'New User') if data else 'New User')
                setattr(profile, 'learning_level', 'beginner')
                setattr(profile, 'created_at', datetime.now(timezone.utc))
                setattr(profile, 'career_interests', [])
                setattr(profile, 'technical_skills', [])
                setattr(profile, 'soft_skills', [])
                setattr(profile, 'certifications', [])
                setattr(profile, 'achievements', [])
                setattr(profile, 'completed_projects', [])
                setattr(profile, 'current_projects', [])
                setattr(profile, 'cognitive_strengths', [])
                setattr(profile, 'preferences', {})
                setattr(profile, 'learning_preferences', {})
                setattr(profile, 'skill_levels', {})
                setattr(profile, 'personality_traits', {})
                db.add(profile)
            
            response = await self._process_onboarding_step(step, profile, data)
            
            # Update profile with new data
            if data:
                self._update_profile(profile, step, data)
            
            db.commit()
            
            return {
                "step": step,
                "next_step": self._get_next_step(step),
                "response": response,
                "profile": {
                    "id": getattr(profile, 'id', ''),
                    "name": getattr(profile, 'name', ''),
                    "learning_level": getattr(profile, 'learning_level', 'beginner'),
                    "career_interests": getattr(profile, 'career_interests', []) or []
                }
            }
            
        except Exception as e:
            logger.error(f"Error in onboarding step {step}: {str(e)}\n{traceback.format_exc()}")
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def _process_onboarding_step(self, step: int, profile: UserProfile, data: Optional[Dict]) -> str:
        """Process each onboarding step and return AI response."""
        if step == OnboardingStep.WELCOME:
            return "Welcome to Ponder! I'll help you get started on your learning journey. First, what's your name?"
            
        elif step == OnboardingStep.BASIC_INFO:
            name = data.get('name') if data else None
            if name:
                return f"Nice to meet you, {name}! What's your current level of experience with programming? (beginner/intermediate/advanced)"
            return "What's your name?"
            
        elif step == OnboardingStep.CAREER_PATH:
            return "What interests you about technology? Let's explore different career paths together. Some popular paths are:\n- Game Development\n- Web Development\n- Machine Learning\n- Mobile App Development\n- DevOps\n- Cybersecurity"
            
        elif step == OnboardingStep.TECHNICAL_BACKGROUND:
            career_interests = getattr(profile, 'career_interests', [])
            career_path = career_interests[0] if career_interests else None
            if career_path:
                return f"Great choice! For {career_path}, it would help to know your experience with relevant technologies. What programming languages or tools have you used before?"
            return "What programming languages or tools have you used before?"
            
        elif step == OnboardingStep.LEARNING_STYLE:
            return "How do you prefer to learn?\n- Visual (videos, diagrams)\n- Reading (documentation, books)\n- Interactive (coding exercises)\n- Project-based (building things)\n- Social (pair programming, discussions)"
            
        elif step == OnboardingStep.GOALS:
            return "What are your learning goals? For example:\n- Build a specific project\n- Master a technology\n- Prepare for a job\n- Learn for fun"
            
        elif step == OnboardingStep.PREFERENCES:
            return "Last few questions about your preferences:\n- How much time can you dedicate to learning each week?\n- Do you prefer structured courses or flexible learning?\n- Are you interested in getting certifications?"
            
        elif step == OnboardingStep.COMPLETE:
            # Generate personalized learning plan
            career_interests = getattr(profile, 'career_interests', [])
            learning_level = getattr(profile, 'learning_level', 'beginner')
            interests_str = ', '.join(career_interests) if career_interests else 'technology'
            return f"Great! Based on your interests in {interests_str} and your {learning_level} level, I'll help you create a personalized learning path. You can always update your preferences later. Let's start with your first learning goal!"
            
        return "Invalid step"

    def _update_profile(self, profile: UserProfile, step: int, data: Dict) -> None:
        """Update profile based on step and data."""
        if step == OnboardingStep.BASIC_INFO:
            if name := data.get('name'):
                setattr(profile, 'name', name)
            if level := data.get('level'):
                setattr(profile, 'learning_level', level)
            
        elif step == OnboardingStep.CAREER_PATH:
            if career_path := data.get('career_path'):
                setattr(profile, 'career_interests', [career_path])
                
        elif step == OnboardingStep.TECHNICAL_BACKGROUND:
            if tech_skills := data.get('skills'):
                setattr(profile, 'technical_skills', tech_skills)
                
        elif step == OnboardingStep.LEARNING_STYLE:
            if style := data.get('learning_style'):
                setattr(profile, 'learning_style', style)
                if preferences := data.get('preferences'):
                    setattr(profile, 'learning_preferences', preferences)
                
        elif step == OnboardingStep.GOALS:
            if goals := data.get('goals'):
                setattr(profile, 'long_term_goals', goals)
                
        elif step == OnboardingStep.PREFERENCES:
            preferences = {}
            if time_commitment := data.get('time_commitment'):
                preferences['time_commitment'] = time_commitment
            if learning_structure := data.get('learning_structure'):
                preferences['learning_structure'] = learning_structure
            if certifications := data.get('certifications'):
                preferences['certifications'] = certifications
            setattr(profile, 'preferences', preferences)
        
        setattr(profile, 'updated_at', datetime.now(timezone.utc))

    def _get_next_step(self, current_step: int) -> int:
        """Get the next step in the onboarding process."""
        if current_step < OnboardingStep.COMPLETE:
            return current_step + 1
        return OnboardingStep.COMPLETE

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile data."""
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            return None
        
        return {
            "id": getattr(profile, 'id', ''),
            "name": getattr(profile, 'name', ''),
            "email": getattr(profile, 'email', ''),
            "learning_level": getattr(profile, 'learning_level', 'beginner'),
            "location": getattr(profile, 'location', ''),
            "bio": getattr(profile, 'bio', ''),
            "career_interests": getattr(profile, 'career_interests', []) or [],
            "technical_skills": getattr(profile, 'technical_skills', []) or [],
            "soft_skills": getattr(profile, 'soft_skills', []) or [],
            "long_term_goals": getattr(profile, 'long_term_goals', []) or [],
            "achievements": getattr(profile, 'achievements', []) or [],
            "preferences": getattr(profile, 'preferences', {}) or {},
            "learning_preferences": getattr(profile, 'learning_preferences', {}) or {},
            "skill_levels": getattr(profile, 'skill_levels', {}) or {},
            "created_at": getattr(profile, 'created_at', None),
            "updated_at": getattr(profile, 'updated_at', None)
        }

    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile with new data."""
        try:
            # Get or create user profile
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                profile = UserProfile()
                setattr(profile, 'id', str(uuid.uuid4()))
                setattr(profile, 'user_id', user_id)
                setattr(profile, 'created_at', datetime.now(timezone.utc))
                self.db.add(profile)

            # Update profile fields
            for key, value in profile_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)

            setattr(profile, 'updated_at', datetime.now(timezone.utc))
            self.db.commit()
            self.db.refresh(profile)

            return self.get_user_profile(user_id)
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user statistics."""
        # This is a placeholder implementation
        # In a real app, you would calculate actual stats from user activity
        return {
            "total_sessions": 0,
            "total_questions": 0,
            "total_learning_paths": 0,
            "learning_time_minutes": 0.0,
            "topics_explored": [],
            "skill_levels": {},
            "last_active": None
        }

    def search_users(self, query: str, limit: int = 10) -> List[User]:
        """Search users by name or email."""
        return self.db.query(User).filter(
            User.name.ilike(f"%{query}%") | User.email.ilike(f"%{query}%")
        ).limit(limit).all()

    async def get_notifications(self, user_id: str) -> Dict[str, int]:
        """Get user notifications."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Get actual notification counts from database
        from ..models import Conversation, UserProject
        
        # Count recent conversations (learning activities)
        learning_count = self.db.query(Conversation).filter(
            Conversation.user_id == str(user_id),
            Conversation.status == 'active'
        ).count()
        
        # Count user projects (progress activities)
        progress_count = self.db.query(UserProject).filter(
            UserProject.user_id == str(user_id)
        ).count()
        
        return {
            "learning_count": learning_count,
            "progress_count": progress_count
        }

    def delete_user_data(self, user_id: str) -> Dict[str, Any]:
        """Delete all user data for privacy compliance."""
        try:
            # Delete user profile
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if profile:
                self.db.delete(profile)

            # Delete user
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                self.db.delete(user)

            self.db.commit()
            return {"status": "success", "message": "User data deleted successfully"}
        except Exception as e:
            logger.error(f"Error deleting user data: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export user data for privacy compliance."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            profile = self.get_user_profile(user_id)
            
            return {
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "created_at": user.created_at,
                    "last_login": getattr(user, 'last_login', None)
                },
                "profile": profile,
                "export_date": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error exporting user data: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_or_create_test(self, user_id: str):
        test = self.db.query(Psychometric).filter(Psychometric.user_id == user_id).first()
        if not test:
            test = Psychometric(user_id=user_id, questions=DEFAULT_QUESTIONS, status="not_started")
            self.db.add(test)
            self.db.commit()
            self.db.refresh(test)
        elif not test.questions or len(test.questions) < len(DEFAULT_QUESTIONS):
            test.questions = DEFAULT_QUESTIONS
            test.status = "not_started"
            self.db.commit()
            self.db.refresh(test)
        return test

    def get_questions(self, user_id: str):
        """Return questions as an array for React frontend."""
        test = self.get_or_create_test(user_id)
        if test.status == "submitted":
            raise HTTPException(status_code=400, detail="Test already submitted")

        # Convert dict to array
        questions_array = [
            {"id": k, "text": v["text"], "options": v["options"]}
            for k, v in test.questions.items()
        ]
        return questions_array

    def submit_test(self, user_id: str, responses: dict):
        test = self.db.query(Psychometric).filter(Psychometric.user_id == user_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="No psychometric test found")
        if test.status == "submitted":
            raise HTTPException(status_code=400, detail="Test already submitted")

        test.responses = responses
        test.status = "submitted"
        self.db.commit()
        self.db.refresh(test)
        return {"message": "Test submitted successfully"}

    def seed_questions(self):
        """Seed all existing users with default questions if missing"""
        tests = self.db.query(Psychometric).all()
        for test in tests:
            if not test.questions or len(test.questions) < len(DEFAULT_QUESTIONS):
                test.questions = DEFAULT_QUESTIONS
                test.status = "not_started"
                self.db.add(test)
        self.db.commit()
        return {"message": "Seeded psychometric questions"}