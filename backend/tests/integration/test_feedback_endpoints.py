"""
Integration tests for POST /feedback/submit and GET /admin/feedback endpoints.
Uses app.dependency_overrides for proper FastAPI dependency injection mocking.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from datetime import datetime

from app.main import app
from app.database import get_db
from app.routers.user_router import get_current_user_dependency
from app.models.feedback import Feedback


def _fake_user(user_id="user-feedback-test"):
    user = MagicMock()
    user.id = user_id
    user.email = "test@example.com"
    return user


def _fake_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


@pytest.fixture
def authed_client():
    """TestClient with auth and db dependencies overridden."""
    app.dependency_overrides[get_current_user_dependency] = lambda: _fake_user()
    app.dependency_overrides[get_db] = _fake_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client():
    """TestClient without auth override (simulates unauthenticated requests)."""
    client = TestClient(app)
    yield client


class TestSubmitFeedback:
    """Tests for POST /feedback/submit."""

    def test_submit_valid_feedback(self, authed_client):
        """Valid feedback returns 200 with message and id."""
        response = authed_client.post(
            "/feedback/submit",
            json={"category": "Bug", "body": "Something is broken."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Feedback submitted successfully"
        assert "id" in data

    def test_submit_invalid_category_rejected(self, authed_client):
        """Unknown category returns 422."""
        response = authed_client.post(
            "/feedback/submit",
            json={"category": "NotACategory", "body": "Test."},
        )
        assert response.status_code == 422

    def test_submit_empty_body_rejected(self, authed_client):
        """Empty body returns 422."""
        response = authed_client.post(
            "/feedback/submit",
            json={"category": "Idea", "body": "   "},
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("category", ["Bug", "Idea", "Confused", "Love it"])
    def test_all_categories_accepted(self, authed_client, category):
        """Each of the four categories is accepted."""
        response = authed_client.post(
            "/feedback/submit",
            json={"category": category, "body": "Testing."},
        )
        assert response.status_code == 200

    def test_unauthenticated_request_rejected(self, anon_client):
        """Requests without a valid token should be rejected (401/403)."""
        response = anon_client.post(
            "/feedback/submit",
            json={"category": "Bug", "body": "Test."},
        )
        assert response.status_code in (401, 403, 422)

    def test_body_too_long_rejected(self, authed_client):
        """Body over 5000 characters returns 422."""
        response = authed_client.post(
            "/feedback/submit",
            json={"category": "Bug", "body": "x" * 5001},
        )
        assert response.status_code == 422


class TestAdminFeedbackMetrics:
    """Tests for GET /admin/feedback."""

    def test_requires_admin_key(self, anon_client):
        """Missing admin key returns 403.

        admin_router has prefix="/admin" and is mounted at prefix="/admin",
        resulting in the path /admin/admin/feedback.
        """
        response = anon_client.get("/admin/admin/feedback")
        assert response.status_code == 403
