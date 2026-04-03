"""
Integration tests for GET /admin/metrics endpoint.

Verifies the endpoint returns the expected JSON shape with all four metric
groups (engagement, activation, retention, satisfaction) and that admin key
authentication is enforced.

Note: admin_router has prefix="/admin" and is mounted at prefix="/admin",
so the effective path is /admin/admin/metrics.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.config import settings


# ── Helpers ───────────────────────────────────────────────────────────────

ADMIN_KEY = settings.ADMIN_API_KEY
METRICS_PATH = "/admin/admin/metrics"


def _make_db_mock():
    """Return a DB mock whose query().filter().scalar() chain returns 0."""
    db = MagicMock()

    class _QMock:
        def __init__(self):
            self._val = 0

        def filter(self, *a, **kw):
            return self

        def scalar(self):
            return self._val

        def all(self):
            return []

    def _query(*args, **kwargs):
        return _QMock()

    db.query = _query

    # execute() used for raw SQL (retention + interest extraction)
    exec_result = MagicMock()
    exec_result.scalar.return_value = 0
    db.execute = MagicMock(return_value=exec_result)

    return db


@pytest.fixture(autouse=True)
def _clear_metrics_cache():
    """Reset the in-process metrics cache before each test."""
    import app.api.admin as admin_mod

    admin_mod._METRICS_CACHE["data"] = None
    admin_mod._METRICS_CACHE["expires_at"] = 0.0
    yield
    admin_mod._METRICS_CACHE["data"] = None
    admin_mod._METRICS_CACHE["expires_at"] = 0.0


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _make_db_mock
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client():
    app.dependency_overrides[get_db] = _make_db_mock
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


# ── Shape tests ───────────────────────────────────────────────────────────

class TestBetaMetricsShape:
    """Verify the response has the required keys and types."""

    def test_returns_200_with_admin_key(self, client):
        resp = client.get(METRICS_PATH, headers={"X-Admin-Key": ADMIN_KEY})
        assert resp.status_code == 200

    def test_top_level_keys_present(self, client):
        data = client.get(
            METRICS_PATH, headers={"X-Admin-Key": ADMIN_KEY}
        ).json()
        assert "generated_at" in data
        assert "cached" in data
        assert "engagement" in data
        assert "activation" in data
        assert "retention" in data
        assert "satisfaction" in data

    def test_engagement_keys(self, client):
        data = client.get(
            METRICS_PATH, headers={"X-Admin-Key": ADMIN_KEY}
        ).json()
        eng = data["engagement"]
        assert "dau" in eng
        assert "wau" in eng
        assert "avg_sessions_per_user_per_day" in eng
        assert "avg_session_length_min" in eng
        assert "avg_messages_per_session" in eng

    def test_activation_keys(self, client):
        data = client.get(
            METRICS_PATH, headers={"X-Admin-Key": ADMIN_KEY}
        ).json()
        act = data["activation"]
        assert "onboarding_completion_rate_pct" in act
        assert "projects_started" in act
        assert "projects_completed" in act
        assert "projects_abandoned" in act
        assert "assessment_completions" in act
        assert "interest_extraction_rate_pct" in act

    def test_retention_keys(self, client):
        data = client.get(
            METRICS_PATH, headers={"X-Admin-Key": ADMIN_KEY}
        ).json()
        ret = data["retention"]
        assert "d1_retention_pct" in ret
        assert "d7_retention_pct" in ret
        assert "d30_retention_pct" in ret

    def test_satisfaction_keys(self, client):
        data = client.get(
            METRICS_PATH, headers={"X-Admin-Key": ADMIN_KEY}
        ).json()
        sat = data["satisfaction"]
        assert "feedback_volume_30d" in sat
        assert "bug_rate_per_100_sessions" in sat

    def test_numeric_types(self, client):
        data = client.get(
            METRICS_PATH, headers={"X-Admin-Key": ADMIN_KEY}
        ).json()
        eng = data["engagement"]
        assert isinstance(eng["dau"], int)
        assert isinstance(eng["wau"], int)
        assert isinstance(eng["avg_session_length_min"], (int, float))
        assert isinstance(data["retention"]["d1_retention_pct"], (int, float))
        assert isinstance(data["satisfaction"]["feedback_volume_30d"], int)

    def test_cached_flag_false_on_first_call(self, client):
        data = client.get(
            METRICS_PATH, headers={"X-Admin-Key": ADMIN_KEY}
        ).json()
        assert data["cached"] is False

    def test_cached_flag_true_on_second_call(self, client):
        client.get(METRICS_PATH, headers={"X-Admin-Key": ADMIN_KEY})
        data = client.get(
            METRICS_PATH, headers={"X-Admin-Key": ADMIN_KEY}
        ).json()
        assert data["cached"] is True


# ── Auth tests ────────────────────────────────────────────────────────────

class TestBetaMetricsAuth:
    """Verify admin key requirement is enforced."""

    def test_missing_key_returns_403(self, anon_client):
        resp = anon_client.get(METRICS_PATH)
        assert resp.status_code == 403

    def test_wrong_key_returns_403(self, anon_client):
        resp = anon_client.get(
            METRICS_PATH, headers={"X-Admin-Key": "not-the-real-key"}
        )
        assert resp.status_code == 403
