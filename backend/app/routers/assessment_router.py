"""
Assessment Router — project-level assessment endpoints.

POST /api/projects/{project_id}/assess   — run LLM assessment, store result
GET  /api/projects/{project_id}/assessment — retrieve latest assessment
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
from ..services.assessment_service import (
    assess_project,
    get_assessment,
    trigger_discovery,
    process_discovery_response,
    get_discovery,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["assessment"])


# --------------------------------------------------------------------------- #
# Response schemas
# --------------------------------------------------------------------------- #

class AssessmentResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    score: int
    completeness_score: Optional[int]
    quality_score: Optional[int]
    skill_alignment_score: Optional[int]
    feedback: Optional[str]
    strengths: List[str]
    improvements: List[str]
    next_steps: List[str]
    recommended_topics: List[str]
    assessment_report: Dict[str, Any]
    assessed_at: str

    class Config:
        from_attributes = True


def _serialize(assessment) -> AssessmentResponse:
    return AssessmentResponse(
        id=assessment.id,
        project_id=assessment.project_id,
        user_id=assessment.user_id,
        score=assessment.score,
        completeness_score=assessment.completeness_score,
        quality_score=assessment.quality_score,
        skill_alignment_score=assessment.skill_alignment_score,
        feedback=assessment.feedback,
        strengths=assessment.strengths or [],
        improvements=assessment.improvements or [],
        next_steps=assessment.next_steps or [],
        recommended_topics=assessment.recommended_topics or [],
        assessment_report=assessment.assessment_report or {},
        assessed_at=assessment.assessed_at.isoformat() if assessment.assessed_at else "",
    )


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

@router.post("/projects/{project_id}/assess", response_model=AssessmentResponse)
def run_assessment(
    project_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    Run a full LLM-based assessment for a project.

    Can be called when the user is ready to submit the project for grading.
    Re-running overwrites the previous assessment for the same (project, user) pair.
    """
    try:
        assessment = assess_project(db=db, project_id=project_id, user_id=current_user.id)
        return _serialize(assessment)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Assessment failed for project %s: %s", project_id, exc)
        raise HTTPException(status_code=500, detail="Assessment failed. Please try again.")


@router.get("/projects/{project_id}/assessment", response_model=AssessmentResponse)
def fetch_assessment(
    project_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Retrieve the latest assessment result for a project."""
    assessment = get_assessment(db=db, project_id=project_id, user_id=current_user.id)
    if not assessment:
        raise HTTPException(status_code=404, detail="No assessment found for this project.")
    return _serialize(assessment)


# --------------------------------------------------------------------------- #
# Discovery conversation — post-project reflection system
# --------------------------------------------------------------------------- #

class TriggerDiscoveryRequest(BaseModel):
    project_id: str
    reason: str = "completed"  # "completed" | "abandoned"


class DiscoveryResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    trigger_reason: str
    triggered_at: Optional[str]
    completed_at: Optional[str]
    conversation_starter: Optional[str]
    enjoyed_aspects: Optional[str]
    struggled_aspects: Optional[str]
    would_continue: Optional[bool]
    engagement_score: Optional[int]
    domains_confirmed: List[str]
    domains_rejected: List[str]

    class Config:
        from_attributes = True


def _serialize_discovery(d) -> DiscoveryResponse:
    return DiscoveryResponse(
        id=d.id,
        project_id=d.project_id,
        user_id=d.user_id,
        trigger_reason=d.trigger_reason,
        triggered_at=d.triggered_at.isoformat() if d.triggered_at else None,
        completed_at=d.completed_at.isoformat() if d.completed_at else None,
        conversation_starter=d.conversation_starter,
        enjoyed_aspects=d.enjoyed_aspects,
        struggled_aspects=d.struggled_aspects,
        would_continue=d.would_continue,
        engagement_score=d.engagement_score,
        domains_confirmed=d.domains_confirmed or [],
        domains_rejected=d.domains_rejected or [],
    )


@router.post("/assessments/trigger", response_model=DiscoveryResponse)
def trigger_discovery_endpoint(
    body: TriggerDiscoveryRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    Trigger a post-project discovery conversation.

    Called automatically when a project status changes to `completed` or `abandoned`.
    Returns the discovery record including the AI conversation starter.
    Idempotent: returns 409 if a discovery already exists for this project.
    """
    try:
        discovery = trigger_discovery(
            db=db,
            project_id=body.project_id,
            user_id=current_user.id,
            reason=body.reason,
        )
        return _serialize_discovery(discovery)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to trigger discovery for project %s: %s", body.project_id, exc)
        raise HTTPException(status_code=500, detail="Failed to trigger discovery.")


class RespondDiscoveryRequest(BaseModel):
    user_response: str


@router.post("/assessments/{discovery_id}/respond", response_model=DiscoveryResponse)
def respond_to_discovery(
    discovery_id: str,
    body: RespondDiscoveryRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    Submit the user's response to the discovery conversation.

    The AI extracts enjoyed/struggled/would-continue and infers domains.
    Triggers an interest model update event for the ML/AI Engineer to consume.
    """
    try:
        discovery = process_discovery_response(
            db=db,
            discovery_id=discovery_id,
            user_response=body.user_response,
        )
        return _serialize_discovery(discovery)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Discovery response processing failed for %s: %s", discovery_id, exc)
        raise HTTPException(status_code=500, detail="Failed to process discovery response.")


@router.get("/assessments/{project_id}", response_model=DiscoveryResponse)
def get_discovery_endpoint(
    project_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Retrieve the discovery record for a given project."""
    discovery = get_discovery(db=db, project_id=project_id)
    if not discovery:
        raise HTTPException(status_code=404, detail="No discovery found for this project.")
    return _serialize_discovery(discovery)
