from sqlalchemy.orm import Session
from app.models.user import UserProfile

def create_or_update_profile(db: Session, data: dict):
    user_id = data.get("user_id")
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if profile:
        # Update existing profile
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
    else:
        # Create new profile
        profile = UserProfile(**{k: v for k, v in data.items() if hasattr(UserProfile, k)})
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile
