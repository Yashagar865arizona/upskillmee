"""
Integration tests for email-based password reset flow.
Covers: forgot-password, reset-password, token TTL, single-use, unknown email.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Fixtures — re-use the SQLite-patched engine from tests/conftest.py
# via the `db_session` fixture.
# ---------------------------------------------------------------------------

@pytest.fixture
def client(db_session):
    """TestClient without triggering lifespan (avoids Redis dependency)."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(db_session):
    """Create a test user in the DB."""
    auth = AuthService(db_session)
    user = User(
        email="reset_test@example.com",
        username="reset_tester",
        name="Reset Tester",
        is_active=True,
        is_verified=True,
        is_email_verified=True,
    )
    user.password_hash = auth.get_password_hash("OldPassword1!")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# POST /api/v1/auth/forgot-password
# ---------------------------------------------------------------------------

class TestForgotPassword:
    """Tests for the forgot-password endpoint."""

    @patch("app.services.email_service.FastMail.send_message", new_callable=AsyncMock)
    def test_unknown_email_returns_success(self, mock_send, client):
        """Unknown email must NOT reveal that it doesn't exist."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nobody@nowhere.com"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_send.assert_not_called()

    @patch("app.services.email_service.FastMail.send_message", new_callable=AsyncMock)
    def test_known_email_sends_reset_link(self, mock_send, client, registered_user):
        """Known email should enqueue a reset email via background task."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": registered_user.email},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    @patch("app.services.email_service.FastMail.send_message", new_callable=AsyncMock)
    def test_token_stored_with_ttl(self, _mock, client, db_session, registered_user):
        """After request, user should have a reset token with an expiry ~15 min in future."""
        client.post(
            "/api/v1/auth/forgot-password",
            json={"email": registered_user.email},
        )
        db_session.refresh(registered_user)
        assert registered_user.reset_password_token is not None
        assert registered_user.reset_password_token_expires is not None

        expires = registered_user.reset_password_token_expires
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        # Expires should be between 14 and 16 minutes from now
        assert timedelta(minutes=14) < (expires - now) < timedelta(minutes=16)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/reset-password
# ---------------------------------------------------------------------------

class TestResetPassword:
    """Tests for the reset-password (confirmation) endpoint."""

    def _setup_token(self, db_session, user, *, minutes_from_now=10):
        """Manually inject a valid reset token for a user."""
        import secrets
        token = secrets.token_urlsafe(32)
        user.reset_password_token = token
        user.reset_password_token_expires = datetime.now(timezone.utc) + timedelta(minutes=minutes_from_now)
        db_session.commit()
        return token

    def test_happy_path_resets_password(self, client, db_session, registered_user):
        """Valid token -> password updated, token cleared."""
        token = self._setup_token(db_session, registered_user)
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "NewPassword1!"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        db_session.refresh(registered_user)
        # Token must be cleared after use
        assert registered_user.reset_password_token is None
        assert registered_user.reset_password_token_expires is None

    def test_new_password_is_usable(self, client, db_session, registered_user):
        """After reset, old password no longer works; new password authenticates."""
        token = self._setup_token(db_session, registered_user)
        client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "BrandNew2!"},
        )

        auth = AuthService(db_session)
        result = auth.authenticate_user(registered_user.email, "BrandNew2!")
        assert result["success"] is True

        # Old password should fail
        old_result = auth.authenticate_user(registered_user.email, "OldPassword1!")
        assert old_result["success"] is False

    def test_invalid_token_returns_400(self, client, db_session, registered_user):
        """Bogus token must return 400."""
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "totally-fake-token-xyz", "new_password": "whatever"},
        )
        assert response.status_code == 400

    def test_expired_token_returns_400(self, client, db_session, registered_user):
        """Token past its TTL must be rejected with 400."""
        token = self._setup_token(db_session, registered_user, minutes_from_now=-1)
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "NewPass123!"},
        )
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    def test_single_use_token_rejected_on_reuse(self, client, db_session, registered_user):
        """Token used once must be cleared; second use returns 400."""
        token = self._setup_token(db_session, registered_user)
        # First use — success
        r1 = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "FirstReset1!"},
        )
        assert r1.status_code == 200

        # Second use — must fail
        r2 = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "SecondReset2!"},
        )
        assert r2.status_code == 400
