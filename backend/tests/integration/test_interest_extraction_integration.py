"""
Integration tests: message → interest extraction → recommendation flow.

These tests wire up InterestExtractionService with a real SQLite in-memory DB
(no LLM network calls — those are mocked) to verify the end-to-end flow:

  user message → extract interests → persist to UserProfile →
  reload into user_context → agent sees interests in recommendations
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.models.user import User, UserProfile
from app.services.interest_extraction_service import InterestExtractionService


# ---------------------------------------------------------------------------
# Fixtures — reuse the shared test_db_engine from conftest.py
# (it already patches ARRAY → JSON for SQLite compatibility)
# ---------------------------------------------------------------------------


@pytest.fixture
def db(db_session):
    """Alias the shared conftest db_session fixture."""
    return db_session


@pytest.fixture
def user(db):
    u = User()
    u.id = "integration-user-001"
    u.email = "integration@test.com"
    u.username = "integration_user"
    u.name = "Integration Tester"
    u.is_verified = True
    u.password_hash = "$2b$12$test.hash.value"
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def user_profile(db, user):
    p = UserProfile()
    p.user_id = user.id
    p.extracted_interests = []
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMessageToInterestFlow:

    @pytest.mark.asyncio
    async def test_extract_stores_interests_to_profile(self, db, user, user_profile):
        """
        Extracted interests must be written to UserProfile.extracted_interests.
        """
        service = InterestExtractionService(db=db)
        # Mock the structured LLM call so we don't hit the network
        service._llm_extract_structured = AsyncMock(
            return_value={
                "domains": {"game development": 0.92},
                "strengths": [],
                "aversions": [],
                "learning_style": None,
            }
        )

        await service.extract_and_store(user.id, "I love building games!")

        db.refresh(user_profile)
        interests = user_profile.extracted_interests
        assert isinstance(interests, list)
        assert len(interests) == 1
        assert interests[0]["name"] == "game development"
        assert interests[0]["count"] == 1

    @pytest.mark.asyncio
    async def test_interests_persist_across_messages(self, db, user, user_profile):
        """
        Multiple messages accumulate interests; duplicates are not added twice.
        """
        service = InterestExtractionService(db=db)

        # Message 1 → game development
        service._llm_extract_structured = AsyncMock(
            return_value={
                "domains": {"game development": 0.9},
                "strengths": [],
                "aversions": [],
                "learning_style": None,
            }
        )
        await service.extract_and_store(user.id, "I want to make games")

        # Message 2 → game development again + startup
        service._llm_extract_structured = AsyncMock(
            return_value={
                "domains": {"game development": 0.95, "startup building": 0.8},
                "strengths": [],
                "aversions": [],
                "learning_style": None,
            }
        )
        await service.extract_and_store(user.id, "I want to start a game studio")

        db.refresh(user_profile)
        interests = user_profile.extracted_interests
        names = {i["name"] for i in interests}

        assert "game development" in names
        assert "startup building" in names
        # game development count should have incremented
        gd = next(i for i in interests if i["name"] == "game development")
        assert gd["count"] >= 2

    @pytest.mark.asyncio
    async def test_get_interests_as_strings_reflects_stored_data(
        self, db, user, user_profile
    ):
        """
        get_interests_as_strings() reads back what was stored.
        """
        user_profile.extracted_interests = [
            {"name": "machine learning", "category": "technical", "confidence": 0.9, "count": 1, "last_seen_at": "x"},
            {"name": "startup", "category": "career", "confidence": 0.8, "count": 1, "last_seen_at": "x"},
        ]
        db.commit()

        service = InterestExtractionService(db=db)
        result = service.get_interests_as_strings(user.id)

        assert "machine learning" in result
        assert "startup" in result

    @pytest.mark.asyncio
    async def test_interests_surfaced_in_user_context(self, db, user, user_profile):
        """
        After extraction, interests can be loaded into a user_context dict
        that agents consume for recommendations.
        """
        user_profile.extracted_interests = [
            {"name": "game dev", "category": "technical", "confidence": 0.95, "count": 3, "last_seen_at": "x"},
        ]
        db.commit()

        service = InterestExtractionService(db=db)
        extracted_names = service.get_interests_as_strings(user.id)

        # Simulate how message_service builds the snapshot
        user_context = {
            "name": user.name,
            "interests": [],
            "career_path": "",
            "skill_level": "beginner",
        }
        user_context["interests"] = list(dict.fromkeys(
            user_context["interests"] + extracted_names
        ))

        assert "game dev" in user_context["interests"]

    @pytest.mark.asyncio
    async def test_llm_failure_does_not_corrupt_existing_interests(
        self, db, user, user_profile
    ):
        """
        If the LLM call fails, existing interests must be returned unchanged.
        """
        original = [
            {"name": "web development", "category": "technical", "confidence": 0.9, "count": 2, "last_seen_at": "x"}
        ]
        user_profile.extracted_interests = original
        db.commit()

        service = InterestExtractionService(db=db)
        service._llm_extract_structured = AsyncMock(side_effect=Exception("network error"))

        result = await service.extract_and_store(user.id, "tell me about web dev")

        assert len(result) == 1
        assert result[0]["name"] == "web development"

        # DB should still have original untouched
        db.refresh(user_profile)
        assert user_profile.extracted_interests == original

    @pytest.mark.asyncio
    async def test_no_interests_extracted_for_generic_message(
        self, db, user, user_profile
    ):
        """
        A casual message with no interest signals should not alter the profile.
        """
        user_profile.extracted_interests = []
        db.commit()

        service = InterestExtractionService(db=db)
        service._llm_extract_structured = AsyncMock(return_value=None)

        result = await service.extract_and_store(user.id, "Hey, how are you doing today?")

        assert result == []
        db.refresh(user_profile)
        assert user_profile.extracted_interests == []
