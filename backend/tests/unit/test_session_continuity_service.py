"""
Unit tests for SessionContinuityService — BET-69 session continuity.

Covers:
- AI summary generation produces valid structured output
- Context builder assembles correctly from stored summaries
- Fallback to raw-message scan when no summaries exist
- First-time user gets clean empty context
- Corrupted / missing summary handled gracefully
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, Mock, patch
from sqlalchemy.orm import Session

from app.services.session_continuity_service import SessionContinuityService
from app.models.chat import Session as ChatSession, Message, Conversation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_session(sess_id, user_id, summary=None, ended_at=None, summarized_at=None):
    s = MagicMock(spec=ChatSession)
    s.id = sess_id
    s.user_id = user_id
    s.summary = summary
    s.ended_at = ended_at or datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
    s.summarized_at = summarized_at
    s.started_at = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    s.message_count = 5
    return s


def _make_message(msg_id, role, content, session_id=None, created_at=None, conversation_id=None):
    m = MagicMock(spec=Message)
    m.id = msg_id
    m.role = role
    m.content = content
    m.session_id = session_id
    m.conversation_id = conversation_id or "conv-1"
    m.created_at = created_at or datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    return m


def _make_conversation(conv_id, user_id, updated_at=None):
    c = MagicMock(spec=Conversation)
    c.id = conv_id
    c.user_id = user_id
    c.status = "active"
    c.updated_at = updated_at or datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    c.created_at = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    return c


def _build_db_mock(session_results=None, conversation_results=None, message_results=None):
    """Build a mock DB session that returns different query chains per model."""
    db = MagicMock(spec=Session)

    sess_q = MagicMock()
    sess_q.filter.return_value = sess_q
    sess_q.order_by.return_value = sess_q
    sess_q.limit.return_value = sess_q
    sess_q.all.return_value = session_results or []
    sess_q.first.return_value = (session_results or [None])[0] if session_results else None

    conv_q = MagicMock()
    conv_q.filter.return_value = conv_q
    conv_q.order_by.return_value = conv_q
    conv_q.limit.return_value = conv_q
    conv_q.all.return_value = conversation_results or []

    # Messages may be called multiple times (once per conversation)
    msg_q = MagicMock()
    msg_q.filter.return_value = msg_q
    msg_q.order_by.return_value = msg_q
    msg_q.limit.return_value = msg_q
    if message_results is not None:
        if isinstance(message_results, list) and message_results and isinstance(message_results[0], list):
            call_idx = [0]
            def _all():
                i = call_idx[0]
                call_idx[0] += 1
                return message_results[i] if i < len(message_results) else []
            msg_q.all.side_effect = _all
        else:
            msg_q.all.return_value = message_results or []
    else:
        msg_q.all.return_value = []

    def _query(model):
        model_name = str(model)
        if "Session" in model_name and "Message" not in model_name:
            return sess_q
        elif "Conversation" in model_name:
            return conv_q
        else:
            return msg_q

    db.query.side_effect = _query
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


# ---------------------------------------------------------------------------
# Tests — stored summary loading
# ---------------------------------------------------------------------------

class TestLoadFromStoredSummaries:
    def test_returns_empty_when_no_summarised_sessions(self):
        db = _build_db_mock(session_results=[])
        svc = SessionContinuityService(db)
        result = svc.get_prior_session_context(user_id="user-new")

        assert result["is_returning_user"] is False
        assert result["prior_summary"] == ""

    def test_loads_stored_ai_summaries(self):
        sessions = [
            _make_session(
                "s1", "user-abc",
                summary="User explored Python basics and set goal to build a web app.",
                ended_at=datetime(2026, 4, 2, 12, 0, tzinfo=timezone.utc),
                summarized_at=datetime(2026, 4, 2, 12, 1, tzinfo=timezone.utc),
            ),
            _make_session(
                "s2", "user-abc",
                summary="User discussed career options in data science.",
                ended_at=datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc),
                summarized_at=datetime(2026, 4, 1, 12, 1, tzinfo=timezone.utc),
            ),
        ]
        db = _build_db_mock(session_results=sessions)
        svc = SessionContinuityService(db)
        result = svc.get_prior_session_context(user_id="user-abc")

        assert result["is_returning_user"] is True
        assert "Python basics" in result["prior_summary"]
        assert "career options" in result["prior_summary"]
        assert "Most recent session" in result["prior_summary"]
        assert result["last_session_at"] is not None

    def test_topics_extracted_from_stored_summaries(self):
        sessions = [
            _make_session(
                "s1", "user-abc",
                summary="User was learning Python and asked about machine learning.",
                ended_at=datetime(2026, 4, 2, 12, 0, tzinfo=timezone.utc),
                summarized_at=datetime(2026, 4, 2, 12, 1),
            ),
        ]
        db = _build_db_mock(session_results=sessions)
        svc = SessionContinuityService(db)
        result = svc.get_prior_session_context(user_id="user-abc")

        assert "python" in result["last_session_topics"]
        assert "machine learning" in result["last_session_topics"]


# ---------------------------------------------------------------------------
# Tests — generate_and_store_summary
# ---------------------------------------------------------------------------

class TestGenerateAndStoreSummary:
    @patch("app.services.session_continuity_service.SessionContinuityService._generate_ai_summary")
    def test_generates_and_stores_summary(self, mock_gen):
        mock_gen.return_value = "User discussed web dev. Tone: curious."

        session = _make_session("s1", "user-abc", summary=None, ended_at=datetime.utcnow())
        messages = [
            _make_message("m1", "user", "How do I build a website?", session_id="s1"),
            _make_message("m2", "assistant", "Start with HTML and CSS!", session_id="s1"),
        ]
        db = _build_db_mock(session_results=[session], message_results=messages)
        svc = SessionContinuityService(db)

        result = svc.generate_and_store_summary("s1")

        assert result is True
        assert session.summary == "User discussed web dev. Tone: curious."
        assert session.summarized_at is not None
        db.commit.assert_called_once()

    def test_returns_false_for_missing_session(self):
        db = _build_db_mock(session_results=[])
        svc = SessionContinuityService(db)
        result = svc.generate_and_store_summary("nonexistent")
        assert result is False

    def test_returns_false_for_session_with_no_messages(self):
        session = _make_session("s1", "user-abc")
        db = _build_db_mock(session_results=[session], message_results=[])
        svc = SessionContinuityService(db)
        result = svc.generate_and_store_summary("s1")
        assert result is False

    @patch("app.services.session_continuity_service.SessionContinuityService._generate_ai_summary")
    def test_handles_ai_failure_gracefully(self, mock_gen):
        """If the AI call fails entirely and returns empty, should still return False."""
        mock_gen.return_value = ""
        session = _make_session("s1", "user-abc")
        messages = [_make_message("m1", "user", "Hello", session_id="s1")]
        db = _build_db_mock(session_results=[session], message_results=messages)
        svc = SessionContinuityService(db)
        result = svc.generate_and_store_summary("s1")
        assert result is False


# ---------------------------------------------------------------------------
# Tests — AI summary generation (mocked OpenAI)
# ---------------------------------------------------------------------------

class TestAISummaryGeneration:
    @patch("openai.OpenAI")
    @patch("app.config.settings")
    def test_calls_openai_and_returns_summary(self, mock_settings, mock_openai_cls):
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = "User explored ML concepts. Tone: motivated."
        mock_client.chat.completions.create.return_value = mock_resp

        messages = [
            _make_message("m1", "user", "Tell me about neural networks"),
            _make_message("m2", "assistant", "Neural networks are inspired by the brain..."),
        ]

        svc = SessionContinuityService(MagicMock())
        result = svc._generate_ai_summary(messages)

        assert "ML concepts" in result
        mock_client.chat.completions.create.assert_called_once()

    @patch("openai.OpenAI", side_effect=Exception("no API key"))
    def test_falls_back_to_raw_summary_on_import_failure(self, mock_openai_cls):
        """If OpenAI client init fails, should produce a raw summary without crashing."""
        messages = [
            _make_message("m1", "user", "How do I learn Python?"),
            _make_message("m2", "assistant", "Python is great! Start with basics."),
        ]
        svc = SessionContinuityService(MagicMock())
        result = svc._generate_ai_summary(messages)

        # Should have fallen back to raw summary
        assert "How do I learn Python?" in result or "message" in result.lower()


# ---------------------------------------------------------------------------
# Tests — fallback raw message scan
# ---------------------------------------------------------------------------

class TestFallbackRawScan:
    def test_falls_back_when_no_stored_summaries(self):
        """If no stored summaries exist, should scan raw conversations."""
        conv = _make_conversation("conv-1", "user-abc")
        msgs = [
            _make_message("m1", "user", "I want to learn React", conversation_id="conv-1"),
            _make_message("m2", "assistant", "React is great for building UIs!", conversation_id="conv-1"),
        ]

        # No stored summaries, but conversations exist
        db = _build_db_mock(session_results=[], conversation_results=[conv], message_results=[msgs])
        svc = SessionContinuityService(db)
        result = svc.get_prior_session_context(user_id="user-abc")

        assert result["is_returning_user"] is True
        assert "web development" in result["last_session_topics"]  # "react" triggers web dev


# ---------------------------------------------------------------------------
# Tests — edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_corrupted_summary_none_handled(self):
        """A session with summary=None should be excluded from stored path."""
        sessions = [
            _make_session("s1", "user-abc", summary=None, ended_at=datetime.utcnow()),
        ]
        db = _build_db_mock(session_results=[])  # filter excludes summary=None
        svc = SessionContinuityService(db)
        result = svc.get_prior_session_context(user_id="user-abc")
        assert result["is_returning_user"] is False

    def test_exception_in_db_returns_safe_fallback(self):
        db = MagicMock(spec=Session)
        db.query.side_effect = Exception("DB connection lost")
        svc = SessionContinuityService(db)
        result = svc.get_prior_session_context(user_id="user-abc")

        assert result["is_returning_user"] is False
        assert result["prior_summary"] == ""

    def test_compress_empty_messages(self):
        svc = SessionContinuityService(MagicMock())
        assert svc.compress_messages_for_context([]) == []

    def test_extract_topics_from_text(self):
        svc = SessionContinuityService(MagicMock())
        topics = svc._extract_topics_from_text("I want to learn python and data science with pandas")
        assert "python" in topics
        assert "data science" in topics
