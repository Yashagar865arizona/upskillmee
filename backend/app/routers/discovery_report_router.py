"""
Discovery Report Router — self-discovery report endpoints.

GET  /api/users/{user_id}/discovery-report  — generate or return cached report (auth required)
GET  /api/reports/{share_token}             — public shareable link (no auth)
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
from ..services.discovery_report_service import (
    generate_report,
    get_report_by_token,
    get_report_by_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["discovery-report"])


# --------------------------------------------------------------------------- #
# Response schemas
# --------------------------------------------------------------------------- #

class DiscoveryReportResponse(BaseModel):
    id: str
    user_id: str
    share_token: str
    interest_patterns: Dict[str, Any]
    strength_signals: Dict[str, Any]
    domains_explored: Dict[str, Any]
    pivot_suggestions: Dict[str, Any]
    narrative_summary: Optional[str]
    project_count_at_generation: int
    generated_at: Optional[str]

    class Config:
        from_attributes = True


def _serialize(report) -> DiscoveryReportResponse:
    return DiscoveryReportResponse(
        id=report.id,
        user_id=report.user_id,
        share_token=report.share_token,
        interest_patterns=report.interest_patterns or {},
        strength_signals=report.strength_signals or {},
        domains_explored=report.domains_explored or {},
        pivot_suggestions=report.pivot_suggestions or {},
        narrative_summary=report.narrative_summary,
        project_count_at_generation=report.project_count_at_generation or 0,
        generated_at=report.generated_at.isoformat() if report.generated_at else None,
    )


# --------------------------------------------------------------------------- #
# Authenticated endpoint
# --------------------------------------------------------------------------- #

@router.get("/users/{user_id}/discovery-report", response_model=DiscoveryReportResponse)
def get_discovery_report(
    user_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    Generate or return a cached self-discovery report.

    Requires at least 3 completed+assessed projects. The report is cached and
    only regenerated when the assessed project count changes.
    """
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view this report.")

    try:
        report = generate_report(db=db, user_id=user_id)
        return _serialize(report)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("Report generation failed for user %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Report generation failed. Please try again.")


# --------------------------------------------------------------------------- #
# Public shareable endpoint (no auth)
# --------------------------------------------------------------------------- #

@router.get("/reports/{share_token}", response_model=DiscoveryReportResponse)
def get_shared_report(
    share_token: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve a self-discovery report via its public share token.

    No authentication required — the token acts as a capability URL.
    """
    report = get_report_by_token(db=db, share_token=share_token)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return _serialize(report)
