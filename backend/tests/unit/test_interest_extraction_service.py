"""
Unit tests for InterestExtractionService.

Covers:
- LLM response parsing
- Interest merging / deduplication logic
- DB persistence (load / save)
- Graceful failure handling
"""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.interest_extraction_service import InterestExtractionService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db_with_profile(profile=None):
    """Return a minimal SQLAlchemy session mock."""
    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.first.return_value = profile
    return db


def _make_profile(interests=None):
    """Return a mock UserProfile."""
    p = MagicMock()
    p.extracted_interests = interests or []
    return p


# ---------------------------------------------------------------------------
# _merge_interests
# ---------------------------------------------------------------------------


class TestMergeInterests:
    """Pure logic tests — no DB or LLM calls."""

    def test_merge_new_into_empty(self):
        new = [{"name": "game development", "category": "technical", "confidence": 0.9}]
        result = InterestExtractionService._merge_interests([], new)

        assert len(result) == 1
        assert result[0]["name"] == "game development"
        assert result[0]["count"] == 1
        assert "last_seen_at" in result[0]

    def test_merge_deduplicates_by_name(self):
        existing = [
            {
                "name": "game development",
                "category": "technical",
                "confidence": 0.7,
                "count": 1,
                "last_seen_at": "2026-01-01T00:00:00+00:00",
            }
        ]
        new = [{"name": "game development", "category": "technical", "confidence": 0.95}]

        result = InterestExtractionService._merge_interests(existing, new)

        assert len(result) == 1
        assert result[0]["confidence"] == 0.95  # higher wins
        assert result[0]["count"] == 2

    def test_merge_case_insensitive(self):
        existing = [
            {
                "name": "game development",
                "category": "technical",
                "confidence": 0.8,
                "count": 1,
                "last_seen_at": "2026-01-01T00:00:00+00:00",
            }
        ]
        new = [{"name": "Game Development", "category": "technical", "confidence": 0.7}]

        result = InterestExtractionService._merge_interests(existing, new)

        assert len(result) == 1

    def test_merge_multiple_new_signals(self):
        new = [
            {"name": "startup", "category": "career", "confidence": 0.85},
            {"name": "react", "category": "technical", "confidence": 0.9},
        ]
        result = InterestExtractionService._merge_interests([], new)

        assert len(result) == 2
        names = {i["name"] for i in result}
        assert names == {"startup", "react"}

    def test_keeps_existing_when_no_overlap(self):
        existing = [
            {
                "name": "machine learning",
                "category": "technical",
                "confidence": 0.9,
                "count": 3,
                "last_seen_at": "2026-01-01T00:00:00+00:00",
            }
        ]
        new = [{"name": "startup", "category": "career", "confidence": 0.8}]

        result = InterestExtractionService._merge_interests(existing, new)

        assert len(result) == 2

    def test_empty_inputs(self):
        assert InterestExtractionService._merge_interests([], []) == []


# ---------------------------------------------------------------------------
# _llm_extract
# ---------------------------------------------------------------------------


class TestLlmExtract:
    """Tests for LLM response parsing."""

    @pytest.fixture
    def service(self):
        return InterestExtractionService(db=MagicMock())

    @pytest.mark.asyncio
    async def test_valid_llm_response(self, service):
        llm_payload = json.dumps(
            [
                {"name": "game development", "category": "technical", "confidence": 0.92},
                {"name": "startup building", "category": "career", "confidence": 0.78},
            ]
        )
        mock_response = MagicMock()
        mock_response.choices[0].message.content = llm_payload

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        service._client = mock_client

        result = await service._llm_extract("I love building games and want to start a company")

        assert len(result) == 2
        assert result[0]["name"] == "game development"
        assert result[1]["name"] == "startup building"

    @pytest.mark.asyncio
    async def test_filters_low_confidence(self, service):
        llm_payload = json.dumps(
            [
                {"name": "high confidence", "category": "technical", "confidence": 0.9},
                {"name": "low confidence", "category": "other", "confidence": 0.3},
            ]
        )
        mock_response = MagicMock()
        mock_response.choices[0].message.content = llm_payload

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service._client = mock_client

        result = await service._llm_extract("some message")

        assert len(result) == 1
        assert result[0]["name"] == "high confidence"

    @pytest.mark.asyncio
    async def test_malformed_json_returns_empty(self, service):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "not json at all"

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service._client = mock_client

        result = await service._llm_extract("some message")

        assert result == []

    @pytest.mark.asyncio
    async def test_empty_array_response(self, service):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "[]"

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service._client = mock_client

        result = await service._llm_extract("just saying hi")

        assert result == []

    @pytest.mark.asyncio
    async def test_unknown_category_defaults_to_other(self, service):
        llm_payload = json.dumps(
            [{"name": "quantum cooking", "category": "weird_category", "confidence": 0.8}]
        )
        mock_response = MagicMock()
        mock_response.choices[0].message.content = llm_payload

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service._client = mock_client

        result = await service._llm_extract("some message")

        assert result[0]["category"] == "other"


# ---------------------------------------------------------------------------
# _load_interests / _save_interests
# ---------------------------------------------------------------------------


class TestDbPersistence:

    def test_load_returns_empty_when_no_profile(self):
        db = _make_db_with_profile(profile=None)
        service = InterestExtractionService(db=db)

        result = service._load_interests("user-123")
        assert result == []

    def test_load_returns_existing_interests(self):
        interests = [
            {"name": "game dev", "category": "technical", "confidence": 0.9, "count": 1, "last_seen_at": "x"}
        ]
        profile = _make_profile(interests=interests)
        db = _make_db_with_profile(profile=profile)
        service = InterestExtractionService(db=db)

        result = service._load_interests("user-123")
        assert result == interests

    def test_load_handles_none_extracted_interests(self):
        profile = _make_profile(interests=None)
        db = _make_db_with_profile(profile=profile)
        service = InterestExtractionService(db=db)

        result = service._load_interests("user-123")
        assert result == []

    def test_save_updates_existing_profile(self):
        profile = _make_profile(interests=[])
        db = _make_db_with_profile(profile=profile)
        service = InterestExtractionService(db=db)

        new_interests = [{"name": "startup", "category": "career", "confidence": 0.85}]
        service._save_interests("user-123", new_interests)

        assert profile.extracted_interests == new_interests
        db.commit.assert_called_once()

    def test_save_creates_profile_when_missing(self):
        db = _make_db_with_profile(profile=None)
        service = InterestExtractionService(db=db)

        interests = [{"name": "react", "category": "technical", "confidence": 0.9}]

        # Patch UserProfile so SQLAlchemy mapper configuration is not triggered
        with patch(
            "app.services.interest_extraction_service.UserProfile"
        ) as mock_profile_cls:
            mock_profile_cls.return_value = MagicMock()
            service._save_interests("user-456", interests)

        db.add.assert_called_once()
        db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# extract_and_store (integration of all parts)
# ---------------------------------------------------------------------------


class TestExtractAndStore:

    @pytest.mark.asyncio
    async def test_returns_merged_interests_on_success(self):
        existing = [
            {
                "name": "machine learning",
                "category": "technical",
                "confidence": 0.9,
                "count": 2,
                "last_seen_at": "2026-01-01T00:00:00+00:00",
            }
        ]
        profile = _make_profile(interests=existing)
        db = _make_db_with_profile(profile=profile)
        service = InterestExtractionService(db=db)

        # Mock LLM extraction
        new_signals = [
            {"name": "game development", "category": "technical", "confidence": 0.88}
        ]
        service._llm_extract = AsyncMock(return_value=new_signals)

        result = await service.extract_and_store("user-123", "I love building games")

        assert len(result) == 2
        names = {i["name"] for i in result}
        assert names == {"machine learning", "game development"}

    @pytest.mark.asyncio
    async def test_returns_existing_on_llm_failure(self):
        existing = [
            {
                "name": "startup",
                "category": "career",
                "confidence": 0.8,
                "count": 1,
                "last_seen_at": "2026-01-01T00:00:00+00:00",
            }
        ]
        profile = _make_profile(interests=existing)
        db = _make_db_with_profile(profile=profile)
        service = InterestExtractionService(db=db)

        # Simulate LLM failure
        service._llm_extract = AsyncMock(side_effect=Exception("OpenAI timeout"))

        result = await service.extract_and_store("user-123", "I want to build a startup")

        assert result == existing  # existing unchanged

    @pytest.mark.asyncio
    async def test_no_update_when_no_signals_extracted(self):
        existing = [
            {
                "name": "startup",
                "category": "career",
                "confidence": 0.8,
                "count": 1,
                "last_seen_at": "2026-01-01T00:00:00+00:00",
            }
        ]
        profile = _make_profile(interests=existing)
        db = _make_db_with_profile(profile=profile)
        service = InterestExtractionService(db=db)

        # LLM returns nothing
        service._llm_extract = AsyncMock(return_value=[])

        result = await service.extract_and_store("user-123", "how are you today")

        # No commit call because no new interests
        db.commit.assert_not_called()
        assert result == existing


# ---------------------------------------------------------------------------
# get_interests_as_strings
# ---------------------------------------------------------------------------


class TestGetInterestsAsStrings:

    def test_returns_flat_name_list(self):
        interests = [
            {"name": "game development", "category": "technical"},
            {"name": "startup", "category": "career"},
        ]
        profile = _make_profile(interests=interests)
        db = _make_db_with_profile(profile=profile)
        service = InterestExtractionService(db=db)

        result = service.get_interests_as_strings("user-123")
        assert result == ["game development", "startup"]

    def test_returns_empty_for_no_profile(self):
        db = _make_db_with_profile(profile=None)
        service = InterestExtractionService(db=db)

        result = service.get_interests_as_strings("user-999")
        assert result == []
