"""
Portfolio Router — portfolio endpoints for project showcase.

GET  /users/{user_id}/portfolio             — public portfolio data (no auth)
POST /users/{user_id}/portfolio/generate    — generate AI summaries (auth required)
POST /users/{user_id}/portfolio/pdf         — generate PDF download (auth required)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..routers.user_router import get_current_user_dependency
from ..services.portfolio_service import (
    generate_portfolio_pdf,
    generate_portfolio_summaries,
    get_portfolio_projects,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["portfolio"])


# --------------------------------------------------------------------------- #
# Response schemas
# --------------------------------------------------------------------------- #

class AssessmentSummary(BaseModel):
    score: int
    completeness_score: Optional[int] = None
    quality_score: Optional[int] = None
    skill_alignment_score: Optional[int] = None
    strengths: List[str] = []
    feedback: Optional[str] = None


class PortfolioProject(BaseModel):
    project_id: str
    title: str
    description: str
    skills: List[str] = []
    completion_date: Optional[str] = None
    portfolio_summary: Optional[str] = None
    assessment: Optional[AssessmentSummary] = None


class PortfolioResponse(BaseModel):
    user_id: str
    projects: List[PortfolioProject]
    total_projects: int


# --------------------------------------------------------------------------- #
# Public endpoint (no auth — shareable URL)
# --------------------------------------------------------------------------- #

@router.get("/users/{user_id}/portfolio", response_model=PortfolioResponse)
def get_portfolio(
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    Return the portfolio for a user. Public — no authentication required.
    """
    projects = get_portfolio_projects(db, user_id)
    return PortfolioResponse(
        user_id=user_id,
        projects=[PortfolioProject(**p) for p in projects],
        total_projects=len(projects),
    )


# --------------------------------------------------------------------------- #
# Authenticated endpoints
# --------------------------------------------------------------------------- #

@router.post("/users/{user_id}/portfolio/generate", response_model=PortfolioResponse)
def generate_summaries(
    user_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    Generate (or regenerate) AI summaries for all completed projects.
    Auth required — only the owner or admin can trigger generation.
    """
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized.")

    projects = generate_portfolio_summaries(db, user_id)
    return PortfolioResponse(
        user_id=user_id,
        projects=[PortfolioProject(**p) for p in projects],
        total_projects=len(projects),
    )


@router.post("/users/{user_id}/portfolio/pdf")
def download_portfolio_pdf(
    user_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    Generate and return a PDF of the user's portfolio.
    Auth required — only the owner or admin can generate PDFs.
    """
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized.")

    user_name = current_user.name or current_user.username or "User"

    try:
        pdf_bytes = generate_portfolio_pdf(db, user_id, user_name)
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="PDF generation is not available. Install reportlab.",
        )
    except Exception as exc:
        logger.error("PDF generation failed for user %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="PDF generation failed.")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=portfolio_{user_id[:8]}.pdf"},
    )
