from pydantic import BaseModel,EmailStr
from typing import List, Optional

class SignInRequest(BaseModel):
    email: str
    password: str

class SignUpRequest(BaseModel):
    # Basic info
    email: str
    password: str
    name: str

    # Cognitive style
    problem_solving: List[str]
    learning_triggers: List[str]

    # Motivation and goals
    learning_motivation: List[str]
    success_metrics: str

    # Learning preferences
    preferred_resources: List[str]
    learning_pace: str

    # Background
    coding_experience: str
    learning_challenges: str

    # Interests
    interest_areas: List[str]
    industry_context: str

    # Working style
    project_preferences: List[str]
    collaboration_style: List[str]

class TokenResponse(BaseModel):
    token: str
    user: dict
    ai_analysis: Optional[dict] = None

class UserUpdateRequest(BaseModel):
    username: Optional[str]
    full_name: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    country: Optional[str]
    city: Optional[str]