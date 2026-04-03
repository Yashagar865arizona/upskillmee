"""
Unit tests for SessionService — session lifecycle with summary generation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call
from sqlalchemy.orm import Session as DBSession

from app.services.session_service import SessionService, INACTIVITY_THRESHOLD_MINUTES
from app.models.chat import Session as ChatSession


def _make_session(sess_id, user_id, started_at=None, ended_at=None, message_count=0):
    s = MagicMock(spec=ChatSession)
    s.id = sess_id
    s.user_id = user_id
    s.started_at = started_at or datetime.utcnow()
    s.ended_at = ended_at
    s.message_count = message_count
    s.summary = None
    s.summarized_at = None
    return s


class TestGetOrCreateSession:
    def test_returns_existing_active_session(self):
        active = _make_session("s1", "u1")
        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.first.return_value = active
        db.query.return_value = q

        svc = SessionService(db)
        result = svc.get_or_create_session("u1")
        assert result.id == "s1"

    def test_creates_new_session_when_none_active(self):
        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        svc = SessionService(db)
        result = svc.get_or_create_session("u1")
        db.add.assert_called_once()
        db.flush.assert_called_once()


class TestRecordMessage:
    def test_increments_message_count(self):
        session = _make_session("s1", "u1", message_count=3)
        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = session
        db.query.return_value = q

        svc = SessionService(db)
        svc.record_message("s1")
        assert session.message_count == 4

    def test_noop_for_missing_session(self):
        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        svc = SessionService(db)
        svc.record_message("nonexistent")  # Should not raise


class TestEndSession:
    def test_marks_ended_at(self):
        session = _make_session("s1", "u1", ended_at=None)
        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = session
        db.query.return_value = q

        svc = SessionService(db)
        svc.end_session("s1")
        assert session.ended_at is not None

    def test_noop_if_already_ended(self):
        ended = datetime.utcnow() - timedelta(hours=1)
        session = _make_session("s1", "u1", ended_at=ended)
        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = session
        db.query.return_value = q

        svc = SessionService(db)
        svc.end_session("s1")
        assert session.ended_at == ended  # Unchanged


class TestEndSessionWithSummary:
    @patch.object(SessionService, "_schedule_summary")
    def test_ends_and_schedules_summary(self, mock_schedule):
        session = _make_session("s1", "u1", ended_at=None)
        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = session
        db.query.return_value = q

        svc = SessionService(db)
        svc.end_session_with_summary("s1")

        assert session.ended_at is not None
        db.commit.assert_called_once()
        mock_schedule.assert_called_once_with("s1")

    @patch.object(SessionService, "_schedule_summary")
    def test_noop_if_already_ended(self, mock_schedule):
        session = _make_session("s1", "u1", ended_at=datetime.utcnow())
        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = session
        db.query.return_value = q

        svc = SessionService(db)
        svc.end_session_with_summary("s1")
        mock_schedule.assert_not_called()


class TestEndStaleSessions:
    @patch.object(SessionService, "_schedule_summary")
    def test_closes_stale_and_schedules_summaries(self, mock_schedule):
        stale1 = _make_session(
            "s1", "u1",
            started_at=datetime.utcnow() - timedelta(minutes=60),
            ended_at=None,
        )
        stale2 = _make_session(
            "s2", "u1",
            started_at=datetime.utcnow() - timedelta(minutes=45),
            ended_at=None,
        )
        db = MagicMock(spec=DBSession)
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [stale1, stale2]
        db.query.return_value = q

        svc = SessionService(db)
        closed = svc.end_stale_sessions("u1")

        assert closed == 2
        assert stale1.ended_at is not None
        assert stale2.ended_at is not None
        assert mock_schedule.call_count == 2
        db.commit.assert_called_once()
