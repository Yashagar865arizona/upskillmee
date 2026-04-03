from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.models.feedback import UserFeedback
import uuid
import shutil
import os
from app.routers.user_router import get_current_user_dependency
from app.models import User

router = APIRouter()

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
