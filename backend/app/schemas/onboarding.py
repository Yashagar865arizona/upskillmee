from pydantic import BaseModel
from typing import List, Dict, Optional


class UserProfileBase(BaseModel):
    # Demographics
    age: Optional[int] = None
    location: Optional[str] = None
    education_level: Optional[str] = None
    languages: List[str] = []
    learning_style: Optional[str] = None

    # Interests and Preferences
    hobbies: List[str] = []
    preferred_subjects: List[str] = []
    work_style: Optional[str] = None
    work_preferences: List[str] = []
    career_interests: List[str] = []
    long_term_goals: List[str] = []

    # Skills and Competencies
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    certifications: List[str] = []
    achievements: List[str] = []

    # Learning Progress
    learning_level: str = "beginner"
    completed_projects: List[str] = []
    current_projects: List[str] = []
    skill_levels: Dict = {}

    
    personality_traits: Dict = {}
    cognitive_strengths: List[str] = []
    learning_preferences: Dict = {}

    
    preferences: Dict = {}



class UserProfileCreate(UserProfileBase):
    pass  



class UserProfileResponse(UserProfileBase):
    id: str
    user_id: str

    class Config:
        orm_mode = True
