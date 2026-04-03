from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, ForeignKey, JSON, DateTime, Integer, func, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from .base_model import BaseModel
from ..database.base import Base
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(BaseModel, Base):
    __tablename__ = "users"
    # Authentication fields
    # id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    phone_number = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    reset_password_token = Column(String, nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    oauth_provider = Column(String, nullable=True)
    otp_code = Column(String, nullable=True)
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)
    pending_email = Column(String, nullable=True)
    pending_phone_number = Column(String, nullable=True)
    # Profile fields
    name = Column(String)
    status = Column(String, default="active")
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    is_onboarding = Column(Boolean, default=False, nullable=False)
    # Relationships
    feedback = relationship("UserFeedback", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    snapshots = relationship("UserSnapshot", back_populates="user", cascade="all, delete-orphan")
    user_projects = relationship("UserProject", back_populates="user", cascade="all, delete-orphan")
    # Added relationships for learning models
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    learning_progress_items = relationship("LearningProgress", back_populates="user", cascade="all, delete-orphan")
    learning_sessions = relationship("LearningSession", back_populates="user", cascade="all, delete-orphan")
    learning_plans = relationship("LearningPlan", back_populates="user", cascade="all, delete-orphan")
    # Analytics relationships
    events = relationship("UserEvent", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    learning_metrics = relationship("LearningMetric", back_populates="user", cascade="all, delete-orphan")
    funnel_steps = relationship("ConversionFunnelStep", back_populates="user", cascade="all, delete-orphan")
    engagement_scores = relationship("EngagementScore", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    psychometric_test = relationship("Psychometric", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserProfile(BaseModel, Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Demographics and Background
    age = Column(Integer, nullable=True)
    location = Column(String, nullable=True)
    education_level = Column(String, nullable=True)
    languages = Column(ARRAY(String), default=list)
    learning_style = Column(String, nullable=True)
    # Interests and Preferences
    hobbies = Column(ARRAY(String), default=list)
    preferred_subjects = Column(ARRAY(String), default=list)
    work_style = Column(String, nullable=True)
    work_preferences = Column(ARRAY(String), default=list)
    career_interests = Column(ARRAY(String), default=list)
    long_term_goals = Column(ARRAY(String), default=list)
    # Skills and Competencies
    technical_skills = Column(ARRAY(String), default=list)
    soft_skills = Column(ARRAY(String), default=list)
    certifications = Column(ARRAY(String), default=list)
    achievements = Column(ARRAY(String), default=list)
    # Learning Progress
    learning_level = Column(String, default='beginner')
    completed_projects = Column(ARRAY(String), default=list)
    current_projects = Column(ARRAY(String), default=list)
    skill_levels = Column(JSON, default=dict)
    # Personality and Preferences
    personality_traits = Column(JSON, default=dict)
    cognitive_strengths = Column(ARRAY(String), default=list)
    learning_preferences = Column(JSON, default=dict)

    # Additional Settings
    preferences = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", back_populates="profile")

class UserProject(BaseModel, Base):
    __tablename__ = "user_projects"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Project Details
    title = Column(String)
    description = Column(String)
    domain = Column(String)
    difficulty = Column(String)
    status = Column(String, default='in_progress')
    # Progress Tracking
    completion_percentage = Column(Integer, default=0)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True), nullable=True)
    # Metrics (stored as JSON for flexibility)
    project_metrics = Column(JSON, default=dict)
    activity_metrics = Column(JSON, default=dict)
    learning_metrics = Column(JSON, default=dict)
    collaboration_metrics = Column(JSON, default=dict)
    # Project Content
    steps = Column(ARRAY(String), default=list)
    resources_used = Column(ARRAY(String), default=list)
    challenges_faced = Column(ARRAY(String), default=list)
    solutions_implemented = Column(ARRAY(String), default=list)
    # Feedback and Assessment
    mentor_feedback = Column(ARRAY(String), default=list)
    peer_feedback = Column(ARRAY(String), default=list)
    self_assessment = Column(JSON, default=dict)
    final_evaluation = Column(JSON, default=dict)
    # Learning Outcomes
    skills_developed = Column(ARRAY(String), default=list)
    key_learnings = Column(ARRAY(String), default=list)
    next_steps = Column(ARRAY(String), default=list)
    # Relationships
    user = relationship("User", back_populates="user_projects")

class UserSnapshot(BaseModel, Base):
    __tablename__ = "user_snapshots"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Snapshot Data
    learning_progress = Column(JSON, default=dict)
    recent_activities = Column(ARRAY(String), default=list)
    skill_improvements = Column(JSON, default=dict)
    engagement_metrics = Column(JSON, default=dict)
    recommended_next_steps = Column(ARRAY(String), default=list)
     # Relationships
    user = relationship("User", back_populates="snapshots")

class Psychometric(BaseModel, Base):
    __tablename__ = "psychometrics"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())    
    questions = Column(JSON, default=dict)
    responses = Column(JSON, default=dict)
    status = Column(String, default="not_started")

    user = relationship("User", back_populates="psychometric_test")

class PendingUserEmail(Base):
    __tablename__ = "pending_user_emails"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    phone_number = Column(String, unique=True, nullable=True)
    message = Column(String)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    is_verified_by_admin = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)


