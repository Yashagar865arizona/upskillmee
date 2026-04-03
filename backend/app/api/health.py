"""
Basic health check endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..services.health_service import HealthService
from ..database import get_db
from typing import Dict

health_router = APIRouter()
health_service = HealthService()

@health_router.get("/")
async def health_check(db: Session = Depends(get_db)) -> Dict:
    """Get basic system health status."""
    return await health_service.check_health(db)
