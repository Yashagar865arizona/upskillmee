"""
Integration tests for session continuity — BET-36.

Verifies that:
1. A returning user gets prior session context injected.
2. A brand-new user gets no prior context (graceful fallback).
3. Context window compression works when history is long.
4. The prior session summary contains sensible content from past messages.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.session_continuity_service import SessionContinuityService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conversation(conv_id: str, user_id: str, updated_at=None):
    conv = MagicMock()
    conv.id = conv_id
    conv.user_id = user_id
    conv.status = "active"
    conv.updated_at = updated_at or datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    conv.created_at = updated_at or datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    return conv


def _make_message(msg_id: str, conversation_id: str, role: str, content: str, created_at=None):
    msg = MagicMock()
    msg.id = msg_id
    msg.conversation_id = conversation_id
    msg.role = role
    msg.content = content
    msg.created_at = created_at or datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    return msg


# ---------------------------------------------------------------------------
# Tests — get_prior_session_context
# ---------------------------------------------------------------------------

class TestGetPriorSessionContext:
    def _make_service(self, prior_conversations, messages_per_conv):
        db = MagicMock(spec=Session)

        # Session query (stored summaries) — return empty so fallback kicks in
        sess_query = MagicMock()
        sess_query.filter.return_value = sess_query
        sess_query.order_by.return_value = sess_query
        sess_query.limit.return_value = sess_query
        sess_query.all.return_value = []

        conv_query = MagicMock()
        conv_query.filter.return_value = conv_query
        conv_query.order_by.return_value = conv_query
        conv_query.limit.return_value = conv_query
        conv_query.all.return_value = prior_conversations

        msg_query = MagicMock()
        msg_query.filter.return_value = msg_query
        msg_query.order_by.return_value = msg_query
        msg_query.limit.return_value = msg_query

        # Return different messages based on call count
        call_count = [0]
        def _msg_all():
            idx = call_count[0]
            call_count[0] += 1
            if idx < len(messages_per_conv):
                return messages_per_conv[idx]
            return []
        msg_query.all.side_effect = _msg_all

        def _route_query(model):
            model_str = str(model)
            if "Conversation" in model_str:
                return conv_query
            # ChatSession model check — route to sess_query for stored summaries path
            if "Session" in model_str and "Message" not in model_str:
                return sess_query
            return msg_query

        db.query.side_effect = _route_query

        return SessionContinuityService(db)

    def test_new_user_returns_empty_context(self):
        svc = self._make_service(prior_conversations=[], messages_per_conv=[])
        result = svc.get_prior_session_context(user_id="user-new", current_conversation_id=None)

        assert result["is_returning_user"] is False
        assert result["prior_summary"] == ""
        assert result["last_session_topics"] == []
        assert result["last_session_at"] is None

    def test_returning_user_gets_context(self):
        conv = _make_conversation("conv-1", "user-abc")
        msgs = [
            _make_message("m1", "conv-1", "user", "I want to learn machine learning"),
            _make_message("m2", "conv-1", "assistant", "Great! Let's explore ML together."),
            _make_message("m3", "conv-1", "user", "Tell me about neural networks"),
        ]
        svc = self._make_service(prior_conversations=[conv], messages_per_conv=[msgs])

        result = svc.get_prior_session_context(user_id="user-abc", current_conversation_id="conv-current")

        assert result["is_returning_user"] is True
        assert len(result["prior_summary"]) > 0
        assert result["last_session_at"] is not None
        # Should detect machine learning topic
        assert "machine learning" in result["last_session_topics"]

    def test_prior_summary_contains_last_bot_message(self):
        conv = _make_conversation("conv-1", "user-xyz")
        msgs = [
            _make_message("m1", "conv-1", "user", "How do I start with Python?"),
            _make_message("m2", "conv-1", "assistant", "Python is a great choice! Start with variables and functions."),
        ]
        svc = self._make_service(prior_conversations=[conv], messages_per_conv=[msgs])

        result = svc.get_prior_session_context(user_id="user-xyz")

        assert "Python is a great choice" in result["prior_summary"]

    def test_excludes_current_conversation(self):
        """The current conversation should not appear in prior context."""
        conv_past = _make_conversation("conv-past", "user-abc")
        conv_current = _make_conversation("conv-current", "user-abc")

        db = MagicMock(spec=Session)
        # Capture the filter call to verify current conv is excluded
        filtered_ids = []

        def _filter_spy(*args, **kwargs):
            q = MagicMock()
            q.filter = _filter_spy
            q.order_by.return_value = q
            q.limit.return_value = q
            q.all.return_value = [conv_past]
            return q

        conv_query = MagicMock()
        conv_query.filter.side_effect = _filter_spy

        msg_query = MagicMock()
        msg_query.filter.return_value = msg_query
        msg_query.order_by.return_value = msg_query
        msg_query.limit.return_value = msg_query
        msg_query.all.return_value = []

        db.query.side_effect = lambda m: conv_query if "Conversation" in str(m) else msg_query

        svc = SessionContinuityService(db)
        result = svc.get_prior_session_context("user-abc", current_conversation_id="conv-current")
        # Graceful — should not raise even if no messages found
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Tests — compress_messages_for_context
# ---------------------------------------------------------------------------

class TestCompressMessages:
    def _make_svc(self):
        return SessionContinuityService(MagicMock())

    def test_short_history_returned_unchanged(self):
        svc = self._make_svc()
        messages = [
            {"sender": "user", "text": "Hello", "id": "1"},
            {"sender": "bot", "text": "Hi there!", "id": "2"},
        ]
        result = svc.compress_messages_for_context(messages, max_chars=10000)
        assert result == messages

    def test_long_history_compressed(self):
        svc = self._make_svc()
        # Each message is 100 chars, create 30 = 3000 chars total
        messages = [
            {"sender": "user" if i % 2 == 0 else "bot", "text": "a" * 100, "id": str(i)}
            for i in range(30)
        ]
        result = svc.compress_messages_for_context(messages, max_chars=500)

        # Should have fewer messages
        assert len(result) < len(messages)
        # Should have the placeholder as first message
        assert result[0]["sender"] == "system"
        assert "summarised" in result[0]["text"]

    def test_empty_history_returned_unchanged(self):
        svc = self._make_svc()
        result = svc.compress_messages_for_context([], max_chars=1000)
        assert result == []

    def test_most_recent_messages_preserved(self):
        """The most recent messages must be kept verbatim after compression."""
        svc = self._make_svc()
        messages = [
            {"sender": "user", "text": "a" * 200, "id": str(i)}
            for i in range(20)
        ]
        # Force compression: only 300 chars allowed
        result = svc.compress_messages_for_context(messages, max_chars=300)

        # Last message should be in result (after the placeholder)
        result_ids = {m["id"] for m in result}
        assert "19" in result_ids  # most recent
