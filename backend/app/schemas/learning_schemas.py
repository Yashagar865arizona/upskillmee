from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional
from datetime import datetime

class LearningProgressBase(BaseModel):
    user_id: int
    topic: str
    progress: float
    completed_at: Optional[datetime] = None

class LearningProgressCreate(LearningProgressBase):
    pass

class LearningProgressUpdate(BaseModel):
    progress: float
    completed_at: Optional[datetime] = None

class LearningProgress(LearningProgressBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LearningSessionBase(BaseModel):
    user_id: int
    start_time: datetime
    duration: int  # in minutes
    topic: str

class LearningSessionCreate(LearningSessionBase):
    pass

class LearningSession(LearningSessionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LearningPlan(BaseModel):
    title: str = Field(..., description="Topic-specific title")
    overview: str = Field(..., description="Brief overview")
    timeline: Dict[str, List[Dict]] = Field(..., description="Structured timeline")
    prerequisites: Dict[str, List[str]] = Field(..., description="Required prerequisites")
