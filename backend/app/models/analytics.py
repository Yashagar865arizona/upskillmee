"""
Analytics models for tracking user events and metrics.
"""

from sqlalchemy import Column, String, DateTime, JSON, Integer, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.base import Base
from .base_model import BaseModel
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
import uuid

class UserEvent(BaseModel, Base):
    """Model for tracking user events and interactions"""
    __tablename__ = "user_events"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_metadata = Column(JSON, default=dict)
    
    # Additional tracking fields
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    referrer = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="events")

    __table_args__ = (
        Index('idx_user_events_user_timestamp', user_id, timestamp),
        Index('idx_user_events_type_timestamp', event_type, timestamp),
        Index('idx_user_events_session', session_id, timestamp),
    )

class UserSession(BaseModel, Base):
    """Model for tracking user sessions"""
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String, unique=True, nullable=False, index=True)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Session metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    device_type = Column(String, nullable=True)  # mobile, desktop, tablet
    browser = Column(String, nullable=True)
    os = Column(String, nullable=True)
    
    # Activity metrics
    page_views = Column(Integer, default=0)
    messages_sent = Column(Integer, default=0)
    actions_taken = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index('idx_user_sessions_user_start', user_id, start_time),
        Index('idx_user_sessions_duration', duration_seconds),
    )

class LearningMetric(BaseModel, Base):
    """Model for tracking learning progress metrics"""
    __tablename__ = "learning_metrics"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String, nullable=False, index=True)  # skill_progress, project_completion, etc.
    metric_name = Column(String, nullable=False)  # specific skill or project name
    value = Column(Float, nullable=False)
    previous_value = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Context information
    context = Column(JSON, default=dict)  # Additional context about the metric
    source = Column(String, nullable=True)  # Where the metric came from (chat, project, assessment)
    
    # Relationships
    user = relationship("User", back_populates="learning_metrics")

    __table_args__ = (
        Index('idx_learning_metrics_user_type', user_id, metric_type),
        Index('idx_learning_metrics_name_timestamp', metric_name, timestamp),
    )

class ConversionFunnelStep(BaseModel, Base):
    """Model for tracking user progress through conversion funnel"""
    __tablename__ = "conversion_funnel_steps"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    step_name = Column(String, nullable=False, index=True)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    time_to_complete_seconds = Column(Integer, nullable=True)  # Time from previous step
    
    # Step metadata
    step_metadata = Column(JSON, default=dict)
    source_event_id = Column(String, nullable=True)  # Reference to the event that triggered this step
    
    # Relationships
    user = relationship("User", back_populates="funnel_steps")

    __table_args__ = (
        Index('idx_funnel_steps_user_step', user_id, step_name),
        Index('idx_funnel_steps_completed', completed_at),
    )

class EngagementScore(BaseModel, Base):
    """Model for storing calculated engagement scores"""
    __tablename__ = "engagement_scores"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Engagement metrics
    overall_score = Column(Float, nullable=False)
    chat_engagement = Column(Float, default=0.0)
    learning_engagement = Column(Float, default=0.0)
    project_engagement = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    
    # Supporting data
    messages_count = Column(Integer, default=0)
    session_count = Column(Integer, default=0)
    active_days = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    
    # Calculation metadata
    calculation_period_days = Column(Integer, default=30)
    calculation_metadata = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="engagement_scores")

    __table_args__ = (
        Index('idx_engagement_scores_user_date', user_id, score_date),
        Index('idx_engagement_scores_overall', overall_score),
    )

class SystemMetric(BaseModel, Base):
    """Model for storing system-wide metrics"""
    __tablename__ = "system_metrics"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    metric_name = Column(String, nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Metric metadata
    metric_type = Column(String, nullable=False)  # performance, usage, error, etc.
    category = Column(String, nullable=True)  # api, database, ai_service, etc.
    metric_metadata = Column(JSON, default=dict)
    
    # Aggregation info
    aggregation_period = Column(String, nullable=True)  # hourly, daily, weekly
    sample_count = Column(Integer, nullable=True)  # For averaged metrics
    
    __table_args__ = (
        Index('idx_system_metrics_name_timestamp', metric_name, timestamp),
        Index('idx_system_metrics_type_category', metric_type, category),
    )