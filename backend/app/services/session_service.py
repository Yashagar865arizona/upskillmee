"""
Session service for beta metrics instrumentation and session continuity.

Manages chat session lifecycle:
- Creates a new Session when a user sends their first message.
- Reuses an active session (< 30 min since last message) or starts a fresh one.
- Increments message_count on every message.
- Marks sessions ended_at when explicitly closed or after 30-min inactivity.
- Triggers async AI summary generation on session end for continuity.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from ..models.chat import Session

logger = logging.getLogger(__name__)

INACTIVITY_THRESHOLD_MINUTES = 30


class SessionService:
    def __init__(self, db: DBSession):
        self.db = db

    def get_or_create_session(self, user_id: str) -> Session:
        """Return the current active session for *user_id*, or create a new one.

        A session is considered active when it has no ended_at AND its last
        inferred activity (started_at + message activity) is within the
        inactivity threshold.  Because we don't store last-activity separately,
        we use started_at as a lower bound: if the session is *open* and was
        created within the last 30 minutes it is still active.  This is a
        deliberate simplification — a proper last_activity_at column can be
        added later without breaking this contract.
        """
        cutoff = datetime.utcnow() - timedelta(minutes=INACTIVITY_THRESHOLD_MINUTES)

        active_session = (
            self.db.query(Session)
            .filter(
                Session.user_id == user_id,
                Session.ended_at.is_(None),
                Session.started_at >= cutoff,
            )
            .order_by(Session.started_at.desc())
            .first()
        )

        if active_session:
            return active_session

        new_session = Session(user_id=user_id, message_count=0)
        self.db.add(new_session)
        self.db.flush()  # get id without full commit so callers can chain
        logger.info("SESSION: created session %s for user %s", new_session.id, user_id)
        return new_session

    def record_message(self, session_id: str) -> None:
        """Increment message_count for *session_id*."""
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if session:
            session.message_count = (session.message_count or 0) + 1

    def end_session(self, session_id: str) -> None:
        """Mark *session_id* as ended (sets ended_at to now)."""
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if session and session.ended_at is None:
            session.ended_at = datetime.utcnow()
            logger.info("SESSION: ended session %s", session_id)

    def end_session_with_summary(self, session_id: str) -> None:
        """Mark *session_id* as ended and trigger async AI summary generation.

        The summary is generated in a background thread so it never blocks the
        caller.  Import of SessionContinuityService is deferred to avoid
        circular imports.
        """
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session or session.ended_at is not None:
            return

        session.ended_at = datetime.utcnow()
        self.db.commit()
        logger.info("SESSION: ended session %s — scheduling summary generation", session_id)

        # Trigger background summary generation
        self._schedule_summary(session_id)

    def _schedule_summary(self, session_id: str) -> None:
        """Spawn a daemon thread to generate and store the session summary."""
        import threading
        from ..database.session import SessionLocal

        def _run() -> None:
            db = SessionLocal()
            try:
                from .session_continuity_service import SessionContinuityService
                svc = SessionContinuityService(db)
                svc.generate_and_store_summary(session_id)
            except Exception:
                logger.exception(
                    "SESSION: background summary generation failed for session %s", session_id
                )
            finally:
                db.close()

        t = threading.Thread(target=_run, daemon=True, name=f"session-summary-{session_id[:8]}")
        t.start()

    def end_stale_sessions(self, user_id: str) -> int:
        """Close all open sessions older than the inactivity threshold.

        Returns the number of sessions closed.  Triggers summary generation
        for each closed session as a background task.
        """
        cutoff = datetime.utcnow() - timedelta(minutes=INACTIVITY_THRESHOLD_MINUTES)
        stale = (
            self.db.query(Session)
            .filter(
                Session.user_id == user_id,
                Session.ended_at.is_(None),
                Session.started_at < cutoff,
            )
            .all()
        )
        now = datetime.utcnow()
        stale_ids = []
        for s in stale:
            s.ended_at = now
            stale_ids.append(s.id)

        if stale_ids:
            self.db.commit()
            logger.info(
                "SESSION: closed %d stale session(s) for user %s", len(stale_ids), user_id
            )
            for sid in stale_ids:
                self._schedule_summary(sid)

        return len(stale_ids)
