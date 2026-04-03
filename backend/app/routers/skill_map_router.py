"""
Skill Map Router — user skill graph endpoints.

GET /api/v1/users/{user_id}/skill-map — returns skill graph data
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..routers.user_router import get_current_user_dependency
from ..services.skill_map_service import get_skill_map

logger = logging.getLogger(__name__)

router = APIRouter(tags=["skill-map"])


# ── Response schemas ───────────────────────────────────────────────────────

class SkillNode(BaseModel):
    id: str
    domain: str
    proficiency: float
    assessment_count: int
    last_assessed_at: Optional[str]


class SkillEdge(BaseModel):
    source: str
    target: str
    weight: int


class DomainInfo(BaseModel):
    skill_count: int
    avg_proficiency: float
    skills: List[str]


class SkillMapSummary(BaseModel):
    total_skills: int
    strongest_domain: Optional[str]
    strongest_skill: Optional[str]


class SkillMapResponse(BaseModel):
    nodes: List[SkillNode]
    edges: List[SkillEdge]
    domains: Dict[str, DomainInfo]
    summary: SkillMapSummary


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/users/{user_id}/skill-map", response_model=SkillMapResponse)
def fetch_skill_map(
    user_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    Return the skill graph for a user.

    Nodes represent skills, edges represent co-occurrence across projects,
    and node size maps to proficiency (0.0–1.0).
    """
    # Users can only view their own skill map (extend later for admin/mentor)
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Cannot view another user's skill map.")

    result = get_skill_map(db=db, user_id=user_id)
    return result
