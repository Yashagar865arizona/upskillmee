"""
Pydantic schemas for request/response models.
These are separate from SQLAlchemy models to avoid circular dependencies.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from enum import Enum

# Message schemas
class MessageType(str, Enum):
    TEXT = "text"
    PROJECT = "project_suggestion"
    LEARNING_PLAN = "learning_plan"
    ERROR = "error"
    SYSTEM = "system"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class MessageContext(BaseModel):
    """Context information for message processing"""
    user_id: str
    level: str = Field(default="beginner")
    interests: List[str] = Field(default_factory=list)
    recent_topics: List[str] = Field(default_factory=list)
    last_project: Optional[str] = None
    career_path: Optional[str] = None
    learning_goals: Optional[List[str]] = None
    
    model_config = ConfigDict(use_enum_values=True)

class MessageRequest(BaseModel):
    """Schema for incoming chat messages with context"""
    content: str
    context: MessageContext
    metadata: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    """Schema for chat response format"""
    type: MessageType
    content: str
    meta_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = ConfigDict(use_enum_values=True)

# User schemas
class UserCreate(BaseModel):
    """Schema for creating a new user"""
    name: str
    email: str

class User(BaseModel):
    """Schema for user data"""
    id: str
    name: str
    email: str
    status: str = "active"

    model_config = ConfigDict(from_attributes=True)

class ChatMessage(BaseModel):
    """Schema for simple chat messages"""
    message: str
    user_id: str = "default_user"

class ChatResponse(BaseModel):
    """Schema for simple chat response format"""
    success: bool
    response: Dict[str, str]

class UserProfileSchema(BaseModel):
    """Schema for user profile data"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    interests: List[str] = []
    skills: Dict[str, float] = {}
    learning_style: Optional[str] = None
    personality_traits: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ProjectSchema(BaseModel):
    """Schema for project data"""
    title: str
    description: str
    domain: str
    difficulty: str
    status: str = "in_progress"
    completion_percentage: int = 0
    steps: List[Dict] = []
    resources_used: List[str] = []
    skills_developed: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class SnapshotSchema(BaseModel):
    """Schema for user snapshot data"""
    user_id: str
    learning_progress: Dict = {}
    recent_activities: List[Dict] = []
    skill_improvements: Dict[str, float] = {}
    engagement_metrics: Dict[str, float] = {}
    recommended_next_steps: List[str] = []
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationSummary(BaseModel):
    """Schema for conversation summary"""
    id: str
    topic: str
    last_message: str
    message_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ConversationMetrics(BaseModel):
    """Schema for conversation metrics"""
    total_messages: int
    average_response_time: float
    topics_covered: List[str]
    learning_progress: Dict[str, float]  # topic -> progress percentage
    last_active: datetime
    
    model_config = ConfigDict(from_attributes=True)
