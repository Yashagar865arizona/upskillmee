"""
Unit tests for InterestExtractionService.

Covers:
- LLM response parsing (flat + structured)
- Interest merging / deduplication logic
- DB persistence (load / save)
- Structured profile update and merge logic
- Assessment signal processing
- Behavioral signal processing
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


def _make_db_with_profile(profile=None, interest_profile=None):
    """Return a minimal SQLAlchemy session mock that handles two model types."""
    db = MagicMock()

    def query_side_effect(model):
        q = MagicMock()
        q.filter.return_value = q
        from app.models.user import UserProfile, UserInterestProfile
        if model is UserProfile:
            q.first.return_value = profile
        elif model is UserInterestProfile:
            q.first.return_value = interest_profile
        else:
            q.first.return_value = None
        return q

    db.query.side_effect = query_side_effect
    return db


def _make_profile(interests=None, profile_id="profile-001"):
    p = MagicMock()
    p.id = profile_id
    p.extracted_interests = interests or []
    p.interest_profile = None
    return p


def _make_interest_profile(**kwargs):
    p = MagicMock()
    p.domains = kwargs.get("domains", {})
    p.strengths = kwargs.get("strengths", [])
    p.aversions = kwargs.get("aversions", [])
    p.learning_style = kwargs.get("learning_style", None)
    p.confidence_level = kwargs.get("confidence_level", 0.0)
    p.signal_count = kwargs.get("signal_count", 0)
    return p


# ---------------------------------------------------------------------------
# _merge_interests (unchanged flat logic)
# ---------------------------------------------------------------------------


class TestMergeInterests:
    def test_merge_new_into_empty(self):
        new = [{"name": "game development", "category": "technical", "confidence": 0.9}]
        result = InterestExtractionService._merge_interests([], new)
        assert len(result) == 1
        assert result[0]["name"] == "game development"
        assert result[0]["count"] == 1
        assert "last_seen_at" in result[0]

    def test_merge_deduplicates_by_name(self):
        existing = [{
            "name": "game development", "category": "technical",
            "confidence": 0.7, "count": 1, "last_seen_at": "2026-01-01T00:00:00+00:00",
        }]
        new = [{"name": "game development", "category": "technical", "confidence": 0.95}]
        result = InterestExtractionService._merge_interests(existing, new)
        assert len(result) == 1
        assert result[0]["confidence"] == 0.95
        assert result[0]["count"] == 2

    def test_merge_case_insensitive(self):
        existing = [{
            "name": "game development", "category": "technical",
            "confidence": 0.8, "count": 1, "last_seen_at": "2026-01-01T00:00:00+00:00",
        }]
        new = [{"name": "Game Development", "category": "technical", "confidence": 0.7}]
        result = InterestExtractionService._merge_interests(existing, new)
        assert len(result) == 1

    def test_empty_inputs(self):
        assert InterestExtractionService._merge_interests([], []) == []

    def test_keeps_existing_when_no_overlap(self):
        existing = [{
            "name": "machine learning", "category": "technical",
            "confidence": 0.9, "count": 3, "last_seen_at": "2026-01-01T00:00:00+00:00",
        }]
        new = [{"name": "startup", "category": "career", "confidence": 0.8}]
        result = InterestExtractionService._merge_interests(existing, new)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# _llm_extract_structured
# ---------------------------------------------------------------------------


class TestLlmExtractStructured:
    @pytest.fixture
    def service(self):
        return InterestExtractionService(db=MagicMock())

    @pytest.mark.asyncio
    async def test_valid_structured_response(self, service):
        payload = json.dumps({
            "domains": {"game development": 0.9, "startup building": 0.75},
            "strengths": ["creative thinking"],
            "aversions": ["repetitive tasks"],
            "learning_style": "hands-on",
        })
        mock_response = MagicMock()
        mock_response.choices[0].message.content = payload
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service._client = mock_client

        result = await service._llm_extract_structured("I love building games!")

        assert result is not None
        assert "game development" in result["domains"]
        assert result["domains"]["game development"] == 0.9
        assert result["strengths"] == ["creative thinking"]
        assert result["aversions"] == ["repetitive tasks"]
        assert result["learning_style"] == "hands-on"

    @pytest.mark.asyncio
    async def test_filters_low_confidence_domains(self, service):
        payload = json.dumps({
            "domains": {"high confidence": 0.9, "low confidence": 0.3},
            "strengths": [],
            "aversions": [],
            "learning_style": None,
        })
        mock_response = MagicMock()
        mock_response.choices[0].message.content = payload
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service._client = mock_client

        result = await service._llm_extract_structured("some message")
        assert result is not None
        assert "low confidence" not in result["domains"]
        assert "high confidence" in result["domains"]

    @pytest.mark.asyncio
    async def test_malformed_json_returns_none(self, service):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "not json at all"
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service._client = mock_client

        result = await service._llm_extract_structured("some message")
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_domains_but_strengths_returns_result(self, service):
        payload = json.dumps({
            "domains": {},
            "strengths": ["attention to detail"],
            "aversions": [],
            "learning_style": None,
        })
        mock_response = MagicMock()
        mock_response.choices[0].message.content = payload
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service._client = mock_client

        result = await service._llm_extract_structured("I pay a lot of attention to details")
        assert result is not None
        assert result["strengths"] == ["attention to detail"]

    @pytest.mark.asyncio
    async def test_invalid_learning_style_set_to_none(self, service):
        payload = json.dumps({
            "domains": {"coding": 0.8},
            "strengths": [],
            "aversions": [],
            "learning_style": "visual",  # invalid value
        })
        mock_response = MagicMock()
        mock_response.choices[0].message.content = payload
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service._client = mock_client

        result = await service._llm_extract_structured("some message")
        assert result["learning_style"] is None


# ---------------------------------------------------------------------------
# _update_structured_profile (merge logic for structured model)
# ---------------------------------------------------------------------------


class TestUpdateStructuredProfile:

    def test_domains_are_merged_with_weighted_update(self):
        interest_profile = _make_interest_profile(
            domains={"game development": 0.5},
            strengths=[], aversions=[], signal_count=2, confidence_level=0.2,
        )
        user_profile = _make_profile()
        db = _make_db_with_profile(user_profile, interest_profile)
        service = InterestExtractionService(db=db)

        raw = {"domains": {"game development": 0.9, "react": 0.7}, "strengths": [], "aversions": [], "learning_style": None}
        service._update_structured_profile("user-1", raw)

        # domain should have been updated
        updated_domains = interest_profile.domains
        assert "game development" in updated_domains
        assert updated_domains["game development"] > 0.5  # boosted
        assert "react" in updated_domains
        db.commit.assert_called()

    def test_strengths_are_deduplicated(self):
        ip = _make_interest_profile(strengths=["creative thinking"], signal_count=1, confidence_level=0.1)
        up = _make_profile()
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        raw = {"domains": {}, "strengths": ["creative thinking", "problem solving"], "aversions": [], "learning_style": None}
        service._update_structured_profile("user-1", raw)

        strengths = ip.strengths
        assert strengths.count("creative thinking") == 1
        assert "problem solving" in strengths

    def test_learning_style_updated_when_provided(self):
        ip = _make_interest_profile(learning_style=None, signal_count=0, confidence_level=0.0)
        up = _make_profile()
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        raw = {"domains": {"coding": 0.8}, "strengths": [], "aversions": [], "learning_style": "hands-on"}
        service._update_structured_profile("user-1", raw)

        assert ip.learning_style == "hands-on"

    def test_signal_count_increments(self):
        ip = _make_interest_profile(signal_count=3, confidence_level=0.3)
        up = _make_profile()
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        raw = {"domains": {"python": 0.8}, "strengths": [], "aversions": [], "learning_style": None}
        service._update_structured_profile("user-1", raw)

        assert ip.signal_count == 4

    def test_confidence_level_capped_at_1(self):
        ip = _make_interest_profile(signal_count=15, confidence_level=1.0)
        up = _make_profile()
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        raw = {"domains": {"ml": 0.9}, "strengths": [], "aversions": [], "learning_style": None}
        service._update_structured_profile("user-1", raw)

        assert ip.confidence_level <= 1.0


# ---------------------------------------------------------------------------
# process_assessment_signals
# ---------------------------------------------------------------------------


class TestProcessAssessmentSignals:

    def test_high_score_boosts_domain(self):
        ip = _make_interest_profile(domains={}, strengths=[], aversions=[], signal_count=0, confidence_level=0.0)
        up = _make_profile()
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        service.process_assessment_signals(
            user_id="user-1",
            strengths=["clear communication"],
            improvements=["testing"],
            recommended_topics=["react", "node"],
            score=85,
            project_domain="web development",
        )

        assert "web development" in ip.domains
        assert ip.domains["web development"] >= 0.2
        assert "clear communication" in ip.strengths
        assert "react" in ip.domains
        db.commit.assert_called()

    def test_low_score_adds_aversion(self):
        ip = _make_interest_profile(domains={}, strengths=[], aversions=[], signal_count=0, confidence_level=0.0)
        up = _make_profile()
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        service.process_assessment_signals(
            user_id="user-1",
            strengths=[],
            improvements=["everything"],
            recommended_topics=[],
            score=30,
            project_domain="backend plumbing",
        )

        assert "backend plumbing" in ip.aversions

    def test_medium_score_no_aversion(self):
        ip = _make_interest_profile(domains={}, strengths=[], aversions=[], signal_count=0, confidence_level=0.0)
        up = _make_profile()
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        service.process_assessment_signals(
            user_id="user-1", strengths=[], improvements=[], recommended_topics=[],
            score=60, project_domain="some domain",
        )

        assert "some domain" not in ip.aversions

    def test_recommended_topics_added_as_medium_confidence_domains(self):
        ip = _make_interest_profile(domains={}, strengths=[], aversions=[], signal_count=0, confidence_level=0.0)
        up = _make_profile()
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        service.process_assessment_signals(
            user_id="user-1", strengths=[], improvements=[],
            recommended_topics=["typescript", "graphql"],
            score=75,
        )

        assert "typescript" in ip.domains
        assert ip.domains["typescript"] == 0.5


# ---------------------------------------------------------------------------
# process_behavioral_signal
# ---------------------------------------------------------------------------


class TestProcessBehavioralSignal:

    def test_completed_fast_boosts_domain(self):
        ip = _make_interest_profile(domains={"python": 0.5}, signal_count=1, confidence_level=0.1)
        up = _make_profile()
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        service.process_behavioral_signal("user-1", "project_completed_fast", domain="python")

        assert ip.domains["python"] > 0.5

    def test_abandoned_early_reduces_domain(self):
        ip = _make_interest_profile(domains={"php": 0.7}, signal_count=1, confidence_level=0.1)
        up = _make_profile()
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        service.process_behavioral_signal("user-1", "project_abandoned_early", domain="php")

        assert ip.domains["php"] < 0.7

    def test_followup_questions_boosts_domain(self):
        ip = _make_interest_profile(domains={}, signal_count=0, confidence_level=0.0)
        up = _make_profile()
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        service.process_behavioral_signal("user-1", "followup_questions_asked", domain="machine learning")

        assert "machine learning" in ip.domains
        assert ip.domains["machine learning"] > 0.0

    def test_no_domain_is_noop(self):
        ip = _make_interest_profile(domains={}, signal_count=0, confidence_level=0.0)
        up = _make_profile()
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        service.process_behavioral_signal("user-1", "project_completed_fast", domain=None)

        db.commit.assert_not_called()


# ---------------------------------------------------------------------------
# get_structured_profile
# ---------------------------------------------------------------------------


class TestGetStructuredProfile:

    def test_returns_dict_when_profile_exists(self):
        ip = _make_interest_profile(
            domains={"game dev": 0.9}, strengths=["creativity"],
            aversions=["backend"], learning_style="hands-on",
            confidence_level=0.6, signal_count=6,
        )
        up = _make_profile()
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        result = service.get_structured_profile("user-1")
        assert result is not None
        assert result["domains"] == {"game dev": 0.9}
        assert result["strengths"] == ["creativity"]
        assert result["aversions"] == ["backend"]
        assert result["learning_style"] == "hands-on"
        assert result["confidence_level"] == 0.6

    def test_returns_none_when_no_user_profile(self):
        db = _make_db_with_profile(None, None)
        service = InterestExtractionService(db=db)

        result = service.get_structured_profile("user-999")
        assert result is None


# ---------------------------------------------------------------------------
# reset_interest_profile
# ---------------------------------------------------------------------------


class TestResetInterestProfile:

    def test_resets_both_flat_and_structured(self):
        ip = _make_interest_profile(
            domains={"game dev": 0.9}, strengths=["creativity"],
            aversions=["backend"], learning_style="hands-on",
            confidence_level=0.6, signal_count=6,
        )
        up = _make_profile(interests=[{"name": "game dev", "category": "technical", "confidence": 0.9}])
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        service.reset_interest_profile("user-1")

        assert up.extracted_interests == []
        assert ip.domains == {}
        assert ip.strengths == []
        assert ip.aversions == []
        assert ip.confidence_level == 0.0
        assert ip.signal_count == 0
        db.commit.assert_called()


# ---------------------------------------------------------------------------
# extract_and_store (integration of all parts, mocked LLM)
# ---------------------------------------------------------------------------


class TestExtractAndStore:

    @pytest.mark.asyncio
    async def test_updates_flat_and_structured_on_success(self):
        ip = _make_interest_profile(domains={}, strengths=[], aversions=[], signal_count=0, confidence_level=0.0)
        up = _make_profile(interests=[])
        db = _make_db_with_profile(up, ip)
        service = InterestExtractionService(db=db)

        service._llm_extract_structured = AsyncMock(return_value={
            "domains": {"game development": 0.9},
            "strengths": ["creative thinking"],
            "aversions": [],
            "learning_style": "hands-on",
        })

        result = await service.extract_and_store("user-1", "I love building games")

        assert any(i["name"] == "game development" for i in result)
        assert ip.signal_count == 1
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_returns_existing_on_llm_failure(self):
        existing = [{"name": "startup", "category": "career", "confidence": 0.8, "count": 1, "last_seen_at": "x"}]
        up = _make_profile(interests=existing)
        db = _make_db_with_profile(up, None)
        service = InterestExtractionService(db=db)
        service._llm_extract_structured = AsyncMock(side_effect=Exception("OpenAI timeout"))

        result = await service.extract_and_store("user-1", "I want to build a startup")
        assert result == existing

    @pytest.mark.asyncio
    async def test_no_update_when_no_signals_extracted(self):
        up = _make_profile(interests=[])
        db = _make_db_with_profile(up, None)
        service = InterestExtractionService(db=db)
        service._llm_extract_structured = AsyncMock(return_value=None)

        result = await service.extract_and_store("user-1", "how are you today")
        db.commit.assert_not_called()
        assert result == []


# ---------------------------------------------------------------------------
# get_interests_as_strings
# ---------------------------------------------------------------------------


class TestGetInterestsAsStrings:

    def test_returns_flat_name_list(self):
        interests = [
            {"name": "game development", "category": "technical"},
            {"name": "startup", "category": "career"},
        ]
        up = _make_profile(interests=interests)
        db = _make_db_with_profile(up)
        service = InterestExtractionService(db=db)

        result = service.get_interests_as_strings("user-123")
        assert result == ["game development", "startup"]

    def test_returns_empty_for_no_profile(self):
        db = _make_db_with_profile(None)
        service = InterestExtractionService(db=db)

        result = service.get_interests_as_strings("user-999")
        assert result == []
