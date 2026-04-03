"""
Integration tests for the project assessment endpoints.
Uses TestClient with FastAPI dependency_overrides for auth and DB.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.main import app
from app.models.project import ProjectAssessment
from app.database import get_db
from app.routers.user_router import get_current_user_dependency


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _fake_user():
    user = MagicMock()
    user.id = "user-abc"
    user.email = "test@example.com"
    return user


def _fake_assessment():
    a = MagicMock(spec=ProjectAssessment)
    a.id = "assess-xyz"
    a.project_id = "proj-123"
    a.user_id = "user-abc"
    a.score = 82
    a.completeness_score = 90
    a.quality_score = 78
    a.skill_alignment_score = 80
    a.feedback = "Good work."
    a.strengths = ["Clean code"]
    a.improvements = ["Add tests"]
    a.next_steps = ["Deploy"]
    a.recommended_topics = ["docker"]
    a.assessment_report = {"overall_score": 82}
    a.assessed_at = datetime(2026, 4, 3, 10, 0, 0)
    return a


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user_dependency] = lambda: _fake_user()
    app.dependency_overrides[get_db] = lambda: MagicMock()
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def unauth_client():
    """Client with no auth overrides — tests unauthenticated access."""
    return TestClient(app)


ASSESS_PATCH = "app.routers.assessment_router.assess_project"
GET_PATCH = "app.routers.assessment_router.get_assessment"


# ---------------------------------------------------------------------------
# POST /api/v1/projects/{id}/assess
# ---------------------------------------------------------------------------

class TestRunAssessment:
    def test_assess_returns_200_with_result(self, client):
        assessment = _fake_assessment()
        with patch(ASSESS_PATCH, return_value=assessment):
            response = client.post("/api/v1/projects/proj-123/assess", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 82
        assert data["project_id"] == "proj-123"
        assert "feedback" in data
        assert isinstance(data["strengths"], list)

    def test_assess_returns_404_when_project_missing(self, client):
        with patch(ASSESS_PATCH, side_effect=ValueError("Project bad-id not found")):
            response = client.post("/api/v1/projects/bad-id/assess", json={})
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_assess_returns_500_on_unexpected_error(self, client):
        with patch(ASSESS_PATCH, side_effect=Exception("DB crash")):
            response = client.post("/api/v1/projects/proj-123/assess", json={})
        assert response.status_code == 500

    def test_assess_requires_auth(self, unauth_client):
        response = unauth_client.post("/api/v1/projects/proj-123/assess", json={})
        assert response.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# GET /api/v1/projects/{id}/assessment
# ---------------------------------------------------------------------------

class TestFetchAssessment:
    def test_fetch_returns_200_when_exists(self, client):
        assessment = _fake_assessment()
        with patch(GET_PATCH, return_value=assessment):
            response = client.get("/api/v1/projects/proj-123/assessment")
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 82
        assert data["assessed_at"] == "2026-04-03T10:00:00"

    def test_fetch_returns_404_when_no_assessment(self, client):
        with patch(GET_PATCH, return_value=None):
            response = client.get("/api/v1/projects/proj-123/assessment")
        assert response.status_code == 404

    def test_fetch_requires_auth(self, unauth_client):
        response = unauth_client.get("/api/v1/projects/proj-123/assessment")
        assert response.status_code in (401, 403, 422)
