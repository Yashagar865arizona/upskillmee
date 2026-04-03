"""
Session endpoints for debugging session context and triggering session end.

Endpoints:
- GET  /api/sessions/context  — returns current session continuity context for the user
- POST /api/sessions/end      — manually signal session end (triggers summary generation)
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..routers.user_router import get_current_user_dependency
from ..models.user import User
from ..services.session_continuity_service import SessionContinuityService
from ..services.session_service import SessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionEndRequest(BaseModel):
    session_id: Optional[str] = None


class SessionContextResponse(BaseModel):
    is_returning_user: bool
    prior_summary: str
    last_session_topics: list
    last_session_at: Optional[str]


class SessionEndResponse(BaseModel):
    ended: bool
    session_id: Optional[str]
    summary_scheduled: bool


@router.get("/context", response_model=SessionContextResponse)
async def get_session_context(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Return the current session continuity context for the authenticated user.

    Useful for debugging — shows what the AI Mentor would see when the user
    starts a new session.
    """
    try:
        svc = SessionContinuityService(db)
        ctx = svc.get_prior_session_context(user_id=current_user.id)
        return SessionContextResponse(**ctx)
    except Exception as e:
        logger.exception("Error fetching session context for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load session context",
        )


@router.post("/end", response_model=SessionEndResponse)
async def end_session(
    body: SessionEndRequest = SessionEndRequest(),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Manually signal session end.

    If `session_id` is provided, that specific session is ended.  Otherwise the
    most recent active session for the user is ended.

    Triggers background AI summary generation for the ended session.
    """
    try:
        session_svc = SessionService(db)

        if body.session_id:
            session_svc.end_session_with_summary(body.session_id)
            return SessionEndResponse(
                ended=True,
                session_id=body.session_id,
                summary_scheduled=True,
            )

        # Find the most recent active session for this user
        from ..models.chat import Session as ChatSession

        active = (
            db.query(ChatSession)
            .filter(
                ChatSession.user_id == current_user.id,
                ChatSession.ended_at.is_(None),
            )
            .order_by(ChatSession.started_at.desc())
            .first()
        )

        if not active:
            return SessionEndResponse(ended=False, session_id=None, summary_scheduled=False)

        session_svc.end_session_with_summary(active.id)
        return SessionEndResponse(
            ended=True,
            session_id=active.id,
            summary_scheduled=True,
        )

    except Exception as e:
        logger.exception("Error ending session for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end session",
        )
