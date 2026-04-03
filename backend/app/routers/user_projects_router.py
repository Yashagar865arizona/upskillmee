from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.onboarding import UserProfileCreate, UserProfileResponse
from app.models.user import UserProfile
from app.database.session import get_db

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

@router.post("/", response_model=UserProfileResponse)
def create_or_update_onboarding(data: UserProfileCreate, db: Session = Depends(get_db)):
    # check if profile already exists for the user
    profile = db.query(UserProfile).filter(UserProfile.user_id == data.user_id).first()

    if profile:
        # update existing profile
        for key, value in data.dict(exclude_unset=True).items():
            setattr(profile, key, value)
    else:
        # create new profile
        profile = UserProfile(**data.dict())
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile
