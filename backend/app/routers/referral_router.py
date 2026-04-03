"""
Referral system router.
GET /api/v1/users/{user_id}/referral — get referral code + stats (auth required)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from ..services.referral_service import ReferralService
from .user_router import get_current_user_dependency

router = APIRouter()


def _get_referral_service(db: Session = Depends(get_db)) -> ReferralService:
    return ReferralService(db)


@router.get("/users/{user_id}/referral", response_model=Dict[str, Any])
async def get_referral_stats(
    user_id: str,
    current_user=Depends(get_current_user_dependency),
    referral_service: ReferralService = Depends(_get_referral_service),
):
    """Return referral code and stats for the authenticated user."""
    if str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        return referral_service.get_referral_stats(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
