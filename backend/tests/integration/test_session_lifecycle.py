"""
Integration tests for session lifecycle — BET-63.

Verifies that:
1. A new session is created when a user sends their first message.
2. A second message within 30 minutes reuses the same session.
3. message_count is incremented correctly.
4. A message after 30 minutes inactivity creates a new session.
5. end_session sets ended_at and does not re-close an already-closed session.
6. end_stale_sessions closes open sessions older than the threshold.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, call, patch
from sqlalchemy.orm import Session as DBSession

from app.services.session_service import SessionService, INACTIVITY_THRESHOLD_MINUTES
from app.models.chat import Session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_session(session_id: str, user_id: str, started_at: datetime, ended_at=None, message_count: int = 0):
    s = MagicMock(spec=Session)
    s.id = session_id
    s.user_id = user_id
    s.started_at = started_at
    s.ended_at = ended_at
    s.message_count = message_count
    return s


def _build_service(query_result):
    """Return a SessionService backed by a mock DB that yields *query_result*."""
    db = MagicMock(spec=DBSession)
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.first.return_value = query_result
    q.all.return_value = query_result if isinstance(query_result, list) else []
    db.query.return_value = q
    return SessionService(db), db, q


# ---------------------------------------------------------------------------
# get_or_create_session
# ---------------------------------------------------------------------------

class TestGetOrCreateSession:
    def test_creates_new_session_when_none_exists(self):
        """No active session → creates and flushes a new one."""
        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.first.return_value = None  # no active session found
        db.query.return_value = q

        svc = SessionService(db)
        result = svc.get_or_create_session("user-1")

        db.add.assert_called_once()
        db.flush.assert_called_once()
        assert result is not None

    def test_reuses_active_session_within_threshold(self):
        """Active session started recently → returned as-is, no new session created."""
        recent_start = datetime.utcnow() - timedelta(minutes=5)
        existing = _make_session("sess-1", "user-1", started_at=recent_start)

        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.first.return_value = existing
        db.query.return_value = q

        svc = SessionService(db)
        result = svc.get_or_create_session("user-1")

        db.add.assert_not_called()
        assert result.id == "sess-1"

    def test_creates_new_session_after_inactivity(self):
        """Active session started > 30 min ago → not returned; new session created."""
        old_start = datetime.utcnow() - timedelta(minutes=INACTIVITY_THRESHOLD_MINUTES + 5)
        # Simulate the DB filter returning None (no session within cutoff)
        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.first.return_value = None  # filter excludes old sessions
        db.query.return_value = q

        svc = SessionService(db)
        result = svc.get_or_create_session("user-1")

        db.add.assert_called_once()
        db.flush.assert_called_once()


# ---------------------------------------------------------------------------
# record_message
# ---------------------------------------------------------------------------

class TestRecordMessage:
    def test_increments_message_count(self):
        existing = _make_session("sess-2", "user-1", datetime.utcnow(), message_count=3)
        svc, db, q = _build_service(existing)

        svc.record_message("sess-2")

        assert existing.message_count == 4

    def test_no_error_when_session_missing(self):
        svc, db, q = _build_service(None)
        # Should not raise
        svc.record_message("nonexistent-id")


# ---------------------------------------------------------------------------
# end_session
# ---------------------------------------------------------------------------

class TestEndSession:
    def test_sets_ended_at(self):
        existing = _make_session("sess-3", "user-1", datetime.utcnow())
        svc, db, q = _build_service(existing)

        svc.end_session("sess-3")

        assert existing.ended_at is not None

    def test_does_not_overwrite_already_ended_session(self):
        already_ended = datetime(2026, 4, 1, 10, 0)
        existing = _make_session("sess-4", "user-1", datetime.utcnow(), ended_at=already_ended)
        svc, db, q = _build_service(existing)

        svc.end_session("sess-4")

        # ended_at should still be the original value
        assert existing.ended_at == already_ended

    def test_no_error_when_session_missing(self):
        svc, db, q = _build_service(None)
        svc.end_session("nonexistent")


# ---------------------------------------------------------------------------
# end_stale_sessions
# ---------------------------------------------------------------------------

class TestEndStaleSessions:
    def test_closes_stale_open_sessions(self):
        old = datetime.utcnow() - timedelta(minutes=INACTIVITY_THRESHOLD_MINUTES + 10)
        stale1 = _make_session("stale-1", "user-1", started_at=old)
        stale2 = _make_session("stale-2", "user-1", started_at=old)

        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [stale1, stale2]
        db.query.return_value = q

        svc = SessionService(db)
        count = svc.end_stale_sessions("user-1")

        assert count == 2
        assert stale1.ended_at is not None
        assert stale2.ended_at is not None

    def test_returns_zero_when_no_stale_sessions(self):
        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        svc = SessionService(db)
        count = svc.end_stale_sessions("user-1")

        assert count == 0
