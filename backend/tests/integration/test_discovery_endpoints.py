"""
Integration tests for the post-project discovery endpoints.

POST /api/v1/assessments/trigger
POST /api/v1/assessments/{id}/respond
GET  /api/v1/assessments/{project_id}
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.database import get_db
from app.models.project import PostProjectDiscovery
from app.routers.user_router import get_current_user_dependency

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_user():
    u = MagicMock()
    u.id = "user-abc"
    u.email = "test@example.com"
    return u


def _fake_db():
    return MagicMock()


def _fake_discovery(completed=False):
    d = MagicMock(spec=PostProjectDiscovery)
    d.id = "disc-xyz"
    d.project_id = "proj-123"
    d.user_id = "user-abc"
    d.trigger_reason = "completed"
    d.triggered_at = datetime(2026, 4, 3, 12, 0, 0, tzinfo=timezone.utc)
    d.completed_at = datetime(2026, 4, 3, 12, 5, 0, tzinfo=timezone.utc) if completed else None
    d.conversation_starter = "How did that project go for you?"
    d.enjoyed_aspects = "building the UI" if completed else None
    d.struggled_aspects = "backend auth" if completed else None
    d.would_continue = True if completed else None
    d.engagement_score = 4 if completed else None
    d.domains_confirmed = ["frontend"] if completed else []
    d.domains_rejected = [] if completed else []
    return d


@pytest.fixture
def client():
    """TestClient with auth + DB dependencies overridden."""
    app.dependency_overrides[get_current_user_dependency] = lambda: _fake_user()
    app.dependency_overrides[get_db] = lambda: _fake_db()
    yield TestClient(app)
    app.dependency_overrides = {}


@pytest.fixture
def anon_client():
    """TestClient with NO dependency overrides (requires real auth)."""
    # Reset overrides so auth middleware is active
    original = app.dependency_overrides.copy()
    app.dependency_overrides = {}
    yield TestClient(app)
    app.dependency_overrides = original


TRIGGER_PATCH = "app.routers.assessment_router.trigger_discovery"
RESPOND_PATCH = "app.routers.assessment_router.process_discovery_response"
GET_PATCH = "app.routers.assessment_router.get_discovery"


# ---------------------------------------------------------------------------
# POST /api/v1/assessments/trigger
# ---------------------------------------------------------------------------

class TestTriggerDiscoveryEndpoint:
    def test_trigger_returns_200_with_discovery(self, client):
        discovery = _fake_discovery()
        with patch(TRIGGER_PATCH, return_value=discovery):
            resp = client.post(
                "/api/v1/assessments/trigger",
                json={"project_id": "proj-123", "reason": "completed"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "disc-xyz"
        assert data["project_id"] == "proj-123"
        assert data["conversation_starter"] == "How did that project go for you?"
        assert data["trigger_reason"] == "completed"

    def test_trigger_returns_409_when_already_exists(self, client):
        with patch(TRIGGER_PATCH, side_effect=ValueError("Discovery already triggered for project proj-123")):
            resp = client.post(
                "/api/v1/assessments/trigger",
                json={"project_id": "proj-123", "reason": "completed"},
            )
        assert resp.status_code == 409
        assert "already triggered" in resp.json()["detail"]

    def test_trigger_returns_500_on_unexpected_error(self, client):
        with patch(TRIGGER_PATCH, side_effect=Exception("DB crash")):
            resp = client.post(
                "/api/v1/assessments/trigger",
                json={"project_id": "proj-123", "reason": "completed"},
            )
        assert resp.status_code == 500

    def test_trigger_requires_auth(self, anon_client):
        resp = anon_client.post(
            "/api/v1/assessments/trigger",
            json={"project_id": "proj-123"},
        )
        assert resp.status_code in (401, 403, 422)

    def test_trigger_supports_abandoned_reason(self, client):
        discovery = _fake_discovery()
        discovery.trigger_reason = "abandoned"
        with patch(TRIGGER_PATCH, return_value=discovery):
            resp = client.post(
                "/api/v1/assessments/trigger",
                json={"project_id": "proj-123", "reason": "abandoned"},
            )
        assert resp.status_code == 200
        assert resp.json()["trigger_reason"] == "abandoned"

    def test_trigger_returns_domains_as_lists(self, client):
        discovery = _fake_discovery()
        with patch(TRIGGER_PATCH, return_value=discovery):
            resp = client.post(
                "/api/v1/assessments/trigger",
                json={"project_id": "proj-123", "reason": "completed"},
            )
        data = resp.json()
        assert isinstance(data["domains_confirmed"], list)
        assert isinstance(data["domains_rejected"], list)


# ---------------------------------------------------------------------------
# POST /api/v1/assessments/{id}/respond
# ---------------------------------------------------------------------------

class TestRespondToDiscovery:
    def test_respond_returns_200_with_parsed_data(self, client):
        completed_discovery = _fake_discovery(completed=True)
        with patch(RESPOND_PATCH, return_value=completed_discovery):
            resp = client.post(
                "/api/v1/assessments/disc-xyz/respond",
                json={"user_response": "I loved building the UI!"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["enjoyed_aspects"] == "building the UI"
        assert data["would_continue"] is True
        assert data["engagement_score"] == 4
        assert "frontend" in data["domains_confirmed"]
        assert data["completed_at"] is not None

    def test_respond_returns_404_when_discovery_not_found(self, client):
        with patch(RESPOND_PATCH, side_effect=ValueError("Discovery missing-id not found")):
            resp = client.post(
                "/api/v1/assessments/missing-id/respond",
                json={"user_response": "test"},
            )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_respond_returns_500_on_unexpected_error(self, client):
        with patch(RESPOND_PATCH, side_effect=Exception("LLM offline")):
            resp = client.post(
                "/api/v1/assessments/disc-xyz/respond",
                json={"user_response": "fine"},
            )
        assert resp.status_code == 500

    def test_respond_requires_auth(self, anon_client):
        resp = anon_client.post(
            "/api/v1/assessments/disc-xyz/respond",
            json={"user_response": "test"},
        )
        assert resp.status_code in (401, 403, 422)

    def test_respond_missing_user_response_returns_422(self, client):
        resp = client.post("/api/v1/assessments/disc-xyz/respond", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/assessments/{project_id}
# ---------------------------------------------------------------------------

class TestGetDiscoveryEndpoint:
    def test_get_returns_200_when_exists(self, client):
        discovery = _fake_discovery(completed=True)
        with patch(GET_PATCH, return_value=discovery):
            resp = client.get("/api/v1/assessments/proj-123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == "proj-123"
        assert data["enjoyed_aspects"] == "building the UI"

    def test_get_returns_404_when_no_discovery(self, client):
        with patch(GET_PATCH, return_value=None):
            resp = client.get("/api/v1/assessments/proj-no-disc")
        assert resp.status_code == 404

    def test_get_requires_auth(self, anon_client):
        resp = anon_client.get("/api/v1/assessments/proj-123")
        assert resp.status_code in (401, 403, 422)

    def test_get_returns_pending_discovery_before_response(self, client):
        pending = _fake_discovery(completed=False)
        with patch(GET_PATCH, return_value=pending):
            resp = client.get("/api/v1/assessments/proj-123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed_at"] is None
        assert data["enjoyed_aspects"] is None
        assert data["conversation_starter"] == "How did that project go for you?"

    def test_get_returns_interest_domains(self, client):
        discovery = _fake_discovery(completed=True)
        with patch(GET_PATCH, return_value=discovery):
            resp = client.get("/api/v1/assessments/proj-123")
        data = resp.json()
        assert isinstance(data["domains_confirmed"], list)
        assert isinstance(data["domains_rejected"], list)
