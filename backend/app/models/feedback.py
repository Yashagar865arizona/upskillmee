"""
Database models for user feedback and rating systems.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base_model import BaseModel
from datetime import datetime
import uuid

from ..database.base import Base


FEEDBACK_CATEGORIES = ("Bug", "Idea", "Confused", "Love it")


class Feedback(Base):
    """Simple in-app feedback widget submissions."""
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id])

class UserFeedback(BaseModel, Base):
    """User feedback submissions"""
    __tablename__ = "user_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    feedback_type = Column(String(50), nullable=False)  # bug_report, feature_request, general, rating
    category = Column(String(100), nullable=True)  # ui, performance, content, etc.
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 scale
    attachment=Column(String,nullable=True)
    page_url = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True)
    feedback_metadata = Column(JSON, nullable=True) # Additional context data
    status = Column(String(50), default="open")  # open, in_review, resolved, closed
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    responses = relationship("FeedbackResponse", back_populates="feedback", cascade="all, delete-orphan")

class FeedbackResponse(Base):
    """Admin responses to user feedback"""
    __tablename__ = "feedback_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feedback_id = Column(UUID(as_uuid=True), ForeignKey("user_feedback.id"), nullable=False)
    admin_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    response_text = Column(Text, nullable=False)
    is_public = Column(Boolean, default=True)  # Whether user can see this response
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    feedback = relationship("UserFeedback", back_populates="responses")
    admin_user = relationship("User", foreign_keys=[admin_user_id])

class UserOnboardingAnalytics(Base):
    """Analytics for user onboarding process"""
    __tablename__ = "user_onboarding_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    step_name = Column(String(100), nullable=False)  # welcome, profile_setup, first_chat, etc.
    step_order = Column(Integer, nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    abandoned_at = Column(DateTime, nullable=True)
    time_spent_seconds = Column(Integer, nullable=True)
    completion_rate = Column(Float, nullable=True)  # 0.0 to 1.0
    drop_off_reason = Column(String(200), nullable=True)
    step_metadata = Column(JSON, nullable=True)  # Step-specific data
    
    # Relationships
    user = relationship("User")

class ABTestExperiment(Base):
    """A/B testing experiments"""
    __tablename__ = "ab_test_experiments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    feature_flag = Column(String(100), nullable=False)  # Feature flag identifier
    variants = Column(JSON, nullable=False)  # List of variant configurations
    traffic_allocation = Column(JSON, nullable=False)  # Percentage allocation per variant
    target_audience = Column(JSON, nullable=True)  # Targeting criteria
    success_metrics = Column(JSON, nullable=False)  # Metrics to track
    status = Column(String(50), default="draft")  # draft, active, paused, completed
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    creator = relationship("User")
    participations = relationship("ABTestParticipation", back_populates="experiment", cascade="all, delete-orphan")

class ABTestParticipation(Base):
    """User participation in A/B tests"""
    __tablename__ = "ab_test_participations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("ab_test_experiments.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    variant = Column(String(100), nullable=False)  # Which variant the user is in
    assigned_at = Column(DateTime, default=datetime.utcnow)
    first_exposure_at = Column(DateTime, nullable=True)  # When user first saw the variant
    conversion_events = Column(JSON, nullable=True)  # Tracked conversion events
    participation_metadata = Column(JSON, nullable=True)  # Additional tracking data
    
    # Relationships
    experiment = relationship("ABTestExperiment", back_populates="participations")
    user = relationship("User")

class UserSupportTicket(Base):
    """User support tickets and chat system"""
    __tablename__ = "user_support_tickets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    ticket_number = Column(String(20), unique=True, nullable=False)  # Auto-generated
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # technical, billing, feature, etc.
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    status = Column(String(50), default="open")  # open, in_progress, waiting, resolved, closed
    assigned_to = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 scale
    satisfaction_comment = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    assigned_agent = relationship("User", foreign_keys=[assigned_to])
    messages = relationship("SupportMessage", back_populates="ticket", cascade="all, delete-orphan")

class SupportMessage(Base):
    """Messages within support tickets"""
    __tablename__ = "support_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("user_support_tickets.id"), nullable=False)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)
    message_text = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Internal notes vs. user-visible
    attachments = Column(JSON, nullable=True)  # File attachments metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ticket = relationship("UserSupportTicket", back_populates="messages")
    sender = relationship("User")

class FeatureUsageAnalytics(Base):
    """Analytics for feature usage and adoption"""
    __tablename__ = "feature_usage_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    feature_name = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)  # viewed, clicked, completed, etc.
    session_id = Column(String(100), nullable=True)
    page_url = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True)
    feature_metadata = Column(JSON, nullable=True)  # Feature-specific data
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")