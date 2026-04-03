"""
Location: upskillmee/backend/app/routers/user_router.py

This module implements user functionality for the FastAPI backend:
- Managing user profiles and data
- Handling user preferences
- Tracking user activity and progress
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timezone
import logging
import uuid
import re
import os
import shutil

from ..database import get_db
from ..services.user_service import UserService
from ..services.auth_service import AuthService
from ..models.user import UserProfile, User
from ..schemas.validation import (
    SecureUserProfile, SecureStringField, EmailField, 
    SecureFileUpload, UUIDField
)
from pydantic import EmailStr
from app.dependencies import get_current_admin_user
logger = logging.getLogger(__name__)

router = APIRouter()

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Enhanced schema models with security validation
class UserSchema(BaseModel):
    id: str
    name: str
    email: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True
class PromoteUserRequest(BaseModel):
    email: EmailStr
class UserCreate(BaseModel):
    name: SecureStringField = Field(..., max_length=100)
    email: EmailField

class Notifications(BaseModel):
    learning_count: int = Field(0, ge=0, le=1000)
    progress_count: int = Field(0, ge=0, le=1000)

class UserProfileUpdate(SecureUserProfile):
    """Enhanced user profile update model with security validation"""
    pass

class ProfileUpdate(BaseModel):
    name: Optional[SecureStringField] = Field(None, max_length=100)
    email: Optional[EmailField] = None
    bio: Optional[SecureStringField] = Field(None, max_length=500)
    
class FileUploadRequest(SecureFileUpload):
    """Enhanced file upload request with security validation"""
    pass
    name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None and not EMAIL_REGEX.match(v):
            raise ValueError('Invalid email format')
        return v

class UserStats(BaseModel):
    total_sessions: int
    total_questions: int
    total_learning_paths: int
    learning_time_minutes: float
    topics_explored: List[str]
    skill_levels: Dict[str, float]
    last_active: Optional[datetime] = None
    
class OnboardingRequest(BaseModel):
    age: Optional[int]
    location: Optional[str]
    education_level: Optional[str]
    languages: List[str] = []
    learning_style: Optional[str]
    hobbies: List[str] = []
    preferred_subjects: List[str] = []
    work_style: Optional[str]
    work_preferences: List[str] = []
    career_interests: List[str] = []
    long_term_goals: List[str] = []
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    certifications: List[str] = []
    achievements: List[str] = []
    personality_traits: Dict = {}
    cognitive_strengths: List[str] = []
    learning_preferences: Dict = {}
    preferences: Dict = {}

class UserWithProfile(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    profile: Optional[Dict[str, Any]] = None
    stats: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Get a properly configured user service instance"""
    return UserService(db)

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get instance of AuthService with proper configuration"""
    return AuthService(db)

def get_current_user_dependency(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Dependency to get the current authenticated user from the bearer token."""
    try:
        user = auth_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.get("/current", response_model=UserSchema)
async def get_current_user(
    user_id: str,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
) -> UserSchema:
    """Get current user data."""
    try:
        # Get user profile first since it's the source of truth
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
            return UserSchema(
                id=user_id,
                name=profile.name or "User",
                email=profile.email,
                avatar_url=f"https://via.placeholder.com/30x30"
            )

        # Fallback to user table if no profile exists
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return UserSchema(
                id=user.id,
                name=user.name or "User",
                email=user.email,
                avatar_url=f"https://via.placeholder.com/30x30"
            )

        # If no user found, raise an exception
        raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications", response_model=Notifications)
async def get_user_notifications(
    user_id: str,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
) -> Notifications:
    """Get user notifications."""
    try:
        notifications = await user_service.get_notifications(user_id)
        return notifications
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=UserSchema)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> UserSchema:
    """Create a new user."""
    try:
        # Check for existing user with same email
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        # Create user
        user_id = str(uuid4())
        user = User(
            id=user_id,
            name=user_data.name,
            email=user_data.email,
            status='active',
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)

        # Create user profile
        profile = UserProfile(
            id=str(uuid4()),
            user_id=user_id,
            name=user_data.name,
            email=user_data.email,
            learning_level='beginner',
            created_at=datetime.now(timezone.utc)
        )
        db.add(profile)

        db.commit()
        db.refresh(user)

        return UserSchema(
            id=user.id,
            name=user.name,
            email=user.email,
            avatar_url=f"https://via.placeholder.com/30x30"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile/{user_id}", response_model=Dict[str, Any])
async def update_user_profile(
    user_id: str,
    profile_update: UserProfileUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update user profile data."""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get existing profile or create new one
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            profile = UserProfile(
                id=str(uuid4()),
                user_id=user_id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(profile)

        # Update profile with new data (only specified fields)
        update_data = profile_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)

        # If name is being updated, also update it in the user table
        if 'name' in update_data and update_data['name']:
            user.name = update_data['name']

        # If email is being updated, also update it in the user table
        if 'email' in update_data and update_data['email']:
            user.email = update_data['email']

        profile.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "status": "success",
            "message": "Profile updated successfully",
            "data": {
                "id": profile.id,
                "user_id": profile.user_id,
                "name": profile.name,
                "email": profile.email,
                "updated_at": profile.updated_at
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/me/avatar")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, Any]:
    """Upload profile picture for the current user."""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Validate file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 5MB")
        
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/avatars"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{current_user.id}_{uuid4()}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update user profile with avatar URL
        avatar_url = f"/uploads/avatars/{filename}"
        profile_data = {"avatar_url": avatar_url}
        user_service.update_user_profile(current_user.id, profile_data)
        
        return {
            "status": "success",
            "message": "Profile picture uploaded successfully",
            "avatar_url": avatar_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me/export")
async def export_user_data(
    current_user: User = Depends(get_current_user_dependency),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, Any]:
    """Export all user data for privacy compliance."""
    try:
        return user_service.export_user_data(current_user.id)
    except Exception as e:
        logger.error(f"Error exporting user data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/me")
async def delete_user_account(
    current_user: User = Depends(get_current_user_dependency),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, Any]:
    """Delete user account and all associated data."""
    try:
        return user_service.delete_user_data(current_user.id)
    except Exception as e:
        logger.error(f"Error deleting user account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user_dependency),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, Any]:
    """Get the current user's profile."""
    try:
        profile = user_service.get_user_profile(current_user.id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/me/profile")
async def update_current_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user_dependency),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, Any]:
    """Update the current user's profile."""
    try:
        update_data = profile_update.dict(exclude_unset=True)
        updated_profile = user_service.update_user_profile(current_user.id, update_data)
        
        return {
            "status": "success",
            "message": "Profile updated successfully",
            "profile": updated_profile
        }
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me/settings")
async def get_user_settings(
    current_user: User = Depends(get_current_user_dependency),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, Any]:
    """Get user settings and preferences."""
    try:
        profile = user_service.get_user_profile(current_user.id)
        if not profile:
            return {"preferences": {}, "settings": {}}
        
        return {
            "preferences": profile.get("preferences", {}),
            "learning_preferences": profile.get("learning_preferences", {}),
            "settings": {
                "learning_level": profile.get("learning_level", "beginner"),
                "location": profile.get("location", ""),
                "bio": profile.get("bio", "")
            }
        }
    except Exception as e:
        logger.error(f"Error getting user settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/me/settings")
async def update_user_settings(
    settings_data: Dict[str, Any],
    current_user: User = Depends(get_current_user_dependency),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, Any]:
    """Update user settings and preferences."""
    try:
        user_service.update_user_profile(current_user.id, settings_data)
        
        return {
            "status": "success",
            "message": "Settings updated successfully"
        }
    except Exception as e:
        logger.error(f"Error updating user settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Create a class-based router for backward compatibility
class UserRouter:
    def __init__(self):
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        # Register all routes on the router
        self.router.add_api_route("/me", self.get_current_user, methods=["GET"], response_model=UserWithProfile)
        self.router.add_api_route("/me/profile", self.update_profile, methods=["PUT"])
        self.router.add_api_route("/me/stats", self.get_user_statistics, methods=["GET"], response_model=UserStats)
        self.router.add_api_route("/search", self.search_users, methods=["GET"], response_model=List[UserWithProfile])
        self.router.add_api_route("/{user_id}", self.get_user_by_id, methods=["GET"], response_model=UserWithProfile)

    async def get_current_user(
        self,
        user_id: str = "current_user",  # This would normally come from auth
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service)
    ) -> UserWithProfile:
        """Get the current authenticated user's data."""
        try:
            # Mock implementation for now
            # In a real app, this would get the current user from auth middleware
            user = user_service.get_user_by_id(user_id)
            if not user:
                # For demo purposes, create a mock user
                user = User(
                    id=user_id if user_id != "current_user" else str(uuid.uuid4()),
                    email="user@example.com",
                    username="example_user",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )

            return UserWithProfile(
                id=user.id,
                email=user.email,
                username=user.username,
                created_at=user.created_at,
                updated_at=user.updated_at,
                profile=user_service.get_user_profile(user.id),
                stats=user_service.get_user_stats(user.id)
            )
        except Exception as e:
            logger.error(f"Error fetching current user: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_profile(
        self,
        profile_data: ProfileUpdate,
        user_id: str = "current_user",  # This would normally come from auth
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service)
    ) -> Dict[str, Any]:
        """Update the user's profile information."""
        try:
            # Mock implementation - in a real app, this would update the actual user profile
            profile = user_service.update_user_profile(
                user_id=user_id,
                profile_data=profile_data.dict(exclude_none=True)
            )

            return {
                "status": "success",
                "message": "Profile updated successfully",
                "profile": profile
            }
        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user_statistics(
        self,
        user_id: str = "current_user",  # This would normally come from auth
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service)
    ) -> UserStats:
        """Get usage statistics for the current user."""
        try:
            # Mock implementation - in a real app, this would fetch actual user stats
            stats = user_service.get_user_stats(user_id)

            if not stats:
                # Return mock stats for demo
                return UserStats(
                    total_sessions=12,
                    total_questions=48,
                    total_learning_paths=3,
                    learning_time_minutes=240.5,
                    topics_explored=["Python", "Data Structures", "Algorithms"],
                    skill_levels={"Python": 0.75, "JavaScript": 0.45, "Data Science": 0.3},
                    last_active=datetime.now(timezone.utc)
                )

            return UserStats(**stats)
        except Exception as e:
            logger.error(f"Error fetching user statistics: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def search_users(
        self,
        query: str = Query(..., min_length=2),
        limit: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service)
    ) -> List[UserWithProfile]:
        """Search for users by name, username, or email."""
        try:
            users = user_service.search_users(query, limit)
            return [
                UserWithProfile(
                    id=user.id,
                    email=user.email,
                    username=user.username,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    profile=user_service.get_user_profile(user.id)
                )
                for user in users
            ]
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user_by_id(
        self,
        user_id: str,
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service)
    ) -> UserWithProfile:
        """Get a specific user by their ID."""
        try:
            user = user_service.get_user_by_id(user_id)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {user_id} not found"
                )

            return UserWithProfile(
                id=user.id,
                email=user.email,
                username=user.username,
                created_at=user.created_at,
                updated_at=user.updated_at,
                profile=user_service.get_user_profile(user.id),
                stats=user_service.get_user_stats(user.id)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching user by ID: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


@router.patch("/promote")
def promote_user(
    data: PromoteUserRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  
):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_admin = True
    db.commit()
    return {"message": f"{user.email} is now an admin."}


@router.post("/onboarding")
def save_onboarding(data: OnboardingRequest, 
                    db: Session = Depends(get_db), 
                    current_user: User = Depends(get_current_user_dependency)):

    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    
    user.is_onboarding = True

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()

    if profile:
        for key, value in data.dict(exclude_unset=True).items():
            if hasattr(profile, key):
                setattr(profile, key, value)
    else:
        profile = UserProfile(
            id=str(uuid4()),
            user_id=user.id,
            **data.dict()
        )
        db.add(profile)

    db.commit()
    db.refresh(profile)

    return {"message": "Onboarding data saved successfully", "profile_id": profile.id, "is_onboarding":user.is_onboarding}


@router.get("/questions")
def fetch_questions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Fetch psychometric questions for the current user."""
    try:
        questions = UserService(db).get_questions(current_user.id)
        return questions 
    except Exception as e:
        logger.error(f"Error fetching questions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch questions")


@router.post("/submit")
def submit_responses(
    responses: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Submit psychometric responses for the current user."""
    try:
        result = UserService(db).submit_test(current_user.id, responses)
        return result
    except Exception as e:
        logger.error(f"Error submitting responses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit responses")





# Create and export the router object with backward compatibility structure
# router = UserRouter()
user_router = router
