"""
Unit tests for the post-project discovery service functions:
  trigger_discovery, process_discovery_response, get_discovery, _emit_interest_event
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.assessment_service import (
    trigger_discovery,
    process_discovery_response,
    get_discovery,
)
from app.models.project import PostProjectDiscovery


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_discovery(
    id="disc-1",
    project_id="proj-1",
    user_id="user-1",
    trigger_reason="completed",
    conversation_starter="How did it go?",
    completed_at=None,
):
    d = MagicMock(spec=PostProjectDiscovery)
    d.id = id
    d.project_id = project_id
    d.user_id = user_id
    d.trigger_reason = trigger_reason
    d.conversation_starter = conversation_starter
    d.triggered_at = datetime.now(timezone.utc)
    d.completed_at = completed_at
    d.enjoyed_aspects = None
    d.struggled_aspects = None
    d.would_continue = None
    d.engagement_score = None
    d.domains_confirmed = []
    d.domains_rejected = []
    return d


def _mock_db_no_existing():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    return db


# ---------------------------------------------------------------------------
# trigger_discovery
# ---------------------------------------------------------------------------

class TestTriggerDiscovery:
    def test_creates_new_discovery_when_none_exists(self):
        db = _mock_db_no_existing()
        result = trigger_discovery(db, "proj-1", "user-1", "completed")
        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert isinstance(result, PostProjectDiscovery)

    def test_raises_if_discovery_already_exists(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = _make_discovery()
        with pytest.raises(ValueError, match="already triggered"):
            trigger_discovery(db, "proj-1", "user-1", "completed")

    def test_sets_conversation_starter(self):
        db = _mock_db_no_existing()
        result = trigger_discovery(db, "proj-1", "user-1", "abandoned")
        assert result.conversation_starter is not None
        assert len(result.conversation_starter) > 0

    def test_stores_trigger_reason(self):
        db = _mock_db_no_existing()
        result = trigger_discovery(db, "proj-1", "user-1", "abandoned")
        assert result.trigger_reason == "abandoned"


# ---------------------------------------------------------------------------
# process_discovery_response
# ---------------------------------------------------------------------------

class TestProcessDiscoveryResponse:
    def _db_with_discovery(self, discovery):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = discovery
        return db

    def test_raises_if_discovery_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="not found"):
            process_discovery_response(db, "missing-id", "I loved it")

    @patch("app.services.assessment_service._emit_interest_event")
    @patch("app.services.assessment_service.openai")
    def test_parses_llm_response_and_stores_fields(self, mock_openai, mock_emit):
        mock_choice = MagicMock()
        mock_choice.message.content = '{"enjoyed_aspects": "building the UI", "struggled_aspects": "SQL joins", "would_continue": true, "engagement_score": 4, "domains_confirmed": ["frontend", "design"], "domains_rejected": ["databases"]}'
        mock_openai.chat.completions.create.return_value.choices = [mock_choice]

        discovery = _make_discovery()
        db = self._db_with_discovery(discovery)

        result = process_discovery_response(db, "disc-1", "I loved building the UI but SQL was hard")

        assert result.enjoyed_aspects == "building the UI"
        assert result.struggled_aspects == "SQL joins"
        assert result.would_continue is True
        assert result.engagement_score == 4
        assert "frontend" in result.domains_confirmed
        assert "databases" in result.domains_rejected
        assert result.completed_at is not None
        mock_emit.assert_called_once()

    @patch("app.services.assessment_service._emit_interest_event")
    @patch("app.services.assessment_service.openai")
    def test_fallback_when_llm_fails(self, mock_openai, mock_emit):
        mock_openai.chat.completions.create.side_effect = Exception("LLM down")
        discovery = _make_discovery()
        db = self._db_with_discovery(discovery)

        result = process_discovery_response(db, "disc-1", "It was okay")

        # Fallback stores raw response and defaults
        assert result.enjoyed_aspects == "It was okay"
        assert result.engagement_score == 3
        assert result.completed_at is not None

    @patch("app.services.assessment_service._emit_interest_event")
    @patch("app.services.assessment_service.openai")
    def test_calls_commit_after_update(self, mock_openai, mock_emit):
        mock_choice = MagicMock()
        mock_choice.message.content = '{"enjoyed_aspects": "fun", "struggled_aspects": null, "would_continue": true, "engagement_score": 5, "domains_confirmed": [], "domains_rejected": []}'
        mock_openai.chat.completions.create.return_value.choices = [mock_choice]

        discovery = _make_discovery()
        db = self._db_with_discovery(discovery)

        process_discovery_response(db, "disc-1", "It was fun!")

        db.commit.assert_called()


# ---------------------------------------------------------------------------
# get_discovery
# ---------------------------------------------------------------------------

class TestGetDiscovery:
    def test_returns_discovery_when_found(self):
        d = _make_discovery()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = d
        result = get_discovery(db, "proj-1")
        assert result is d

    def test_returns_none_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = get_discovery(db, "proj-no-discovery")
        assert result is None
