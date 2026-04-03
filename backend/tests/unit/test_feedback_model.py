"""
Unit tests for the Feedback model and FeedbackCreate validator.
"""

import pytest
import uuid
from datetime import datetime

from app.models.feedback import Feedback, FEEDBACK_CATEGORIES
from app.routers.feedback_router import FeedbackCreate
from pydantic import ValidationError


class TestFeedbackModel:
    """Tests for the Feedback SQLAlchemy model."""

    def test_feedback_creation(self, test_db_session, test_user):
        """Feedback can be created and persisted."""
        entry = Feedback(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            category="Bug",
            body="The button is broken.",
        )
        test_db_session.add(entry)
        test_db_session.commit()
        test_db_session.refresh(entry)

        assert entry.id is not None
        assert entry.user_id == test_user.id
        assert entry.category == "Bug"
        assert entry.body == "The button is broken."
        assert isinstance(entry.created_at, datetime)

    def test_feedback_requires_user_id(self, test_db_session):
        """Feedback without user_id raises an integrity error."""
        from sqlalchemy.exc import IntegrityError

        entry = Feedback(
            id=str(uuid.uuid4()),
            category="Idea",
            body="More colors please.",
        )
        test_db_session.add(entry)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
        test_db_session.rollback()

    def test_feedback_categories_constant(self):
        """FEEDBACK_CATEGORIES contains the four expected values."""
        assert set(FEEDBACK_CATEGORIES) == {"Bug", "Idea", "Confused", "Love it"}


class TestFeedbackCreate:
    """Tests for FeedbackCreate Pydantic schema."""

    def test_valid_payload(self):
        """Valid category + body should parse cleanly."""
        data = FeedbackCreate(category="Bug", body="Something crashed.")
        assert data.category == "Bug"
        assert data.body == "Something crashed."

    @pytest.mark.parametrize("category", ["Bug", "Idea", "Confused", "Love it"])
    def test_all_valid_categories(self, category):
        data = FeedbackCreate(category=category, body="Test body.")
        assert data.category == category

    def test_invalid_category_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            FeedbackCreate(category="Unknown", body="Test.")
        assert "category" in str(exc_info.value)

    def test_empty_body_rejected(self):
        with pytest.raises(ValidationError):
            FeedbackCreate(category="Bug", body="   ")

    def test_body_strips_whitespace(self):
        data = FeedbackCreate(category="Idea", body="  hello  ")
        assert data.body == "hello"

    def test_body_too_long_rejected(self):
        with pytest.raises(ValidationError):
            FeedbackCreate(category="Bug", body="x" * 5001)
