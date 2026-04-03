from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.models.feedback import UserFeedback, Feedback, FEEDBACK_CATEGORIES
import uuid
import shutil
import os
from app.routers.user_router import get_current_user_dependency
from app.models import User
from pydantic import BaseModel, field_validator

router = APIRouter()


class FeedbackCreate(BaseModel):
    category: str
    body: str

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in FEEDBACK_CATEGORIES:
            raise ValueError(f"category must be one of {FEEDBACK_CATEGORIES}")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("body must not be empty")
        if len(v) > 5000:
            raise ValueError("body must be 5000 characters or fewer")
        return v


@router.post("/submit", response_model=dict)
def submit_simple_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    """Simple feedback widget endpoint: category + body."""
    entry = Feedback(
        id=uuid.uuid4(),
        user_id=current_user.id,
        category=payload.category,
        body=payload.body,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"message": "Feedback submitted successfully", "id": str(entry.id)}

UPLOAD_DIR = "uploads/feedback"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/", response_model=dict)
def submit_feedback(
    feedback_type: str = Form(...),
    category: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    rating: Optional[int] = Form(None),
    page_url: Optional[str] = Form(None),
    user_agent: Optional[str] = Form(None),
    attachment: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    new_feedback = UserFeedback(
        id=uuid.uuid4(),
        user_id=current_user.id,
        feedback_type=feedback_type,
        category=category,
        title=title,
        description=description,
        rating=rating,
        page_url=page_url,
        user_agent=user_agent,
    )
    if attachment:
        filename = f"{new_feedback.id}_{attachment.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(attachment.file, buffer)
        new_feedback.attachment = file_path

    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return {"message": "Feedback submitted successfully", "id": str(new_feedback.id)}
feedback_router=router
