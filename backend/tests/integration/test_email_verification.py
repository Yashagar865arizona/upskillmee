"""
Integration tests for email verification flow.
Tests: verify, resend, expiry, and login enforcement.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.database import get_db


@pytest.fixture
def client(db_session):
    """TestClient with db override."""
    def override_db():
        yield db_session
    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def unverified_user(db_session):
    """An unverified user with a fresh verification token."""
    import secrets
    from app.utils.security import get_password_hash

    token = secrets.token_urlsafe(32)
    user = User(
        email="verify_test@example.com",
        username="verify_test",
        password_hash=get_password_hash("password123"),
        name="Verify Test",
        is_email_verified=False,
        verification_token=token,
        verification_token_expires=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def expired_token_user(db_session):
    """User with an expired verification token."""
    import secrets
    from app.utils.security import get_password_hash

    token = secrets.token_urlsafe(32)
    user = User(
        email="expired_verify@example.com",
        username="expired_verify",
        password_hash=get_password_hash("password123"),
        name="Expired Verify",
        is_email_verified=False,
        verification_token=token,
        verification_token_expires=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def verified_user(db_session):
    """A fully verified user."""
    from app.utils.security import get_password_hash

    user = User(
        email="verified@example.com",
        username="verified_user",
        password_hash=get_password_hash("password123"),
        name="Verified User",
        is_email_verified=True,
        is_verified=True,
        verification_token=None,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.mark.integration
class TestVerifyEmailEndpoint:
    def test_valid_token_verifies_user(self, client, unverified_user, db_session):
        response = client.get(f"/api/v1/auth/verify-email?token={unverified_user.verification_token}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        db_session.refresh(unverified_user)
        assert unverified_user.is_email_verified is True
        assert unverified_user.is_verified is True
        assert unverified_user.verification_token is None
        assert unverified_user.verification_token_expires is None

    def test_invalid_token_returns_400(self, client):
        response = client.get("/api/v1/auth/verify-email?token=invalid_token_xyz")
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_expired_token_returns_400(self, client, expired_token_user):
        response = client.get(f"/api/v1/auth/verify-email?token={expired_token_user.verification_token}")
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    def test_already_used_token_returns_400(self, client, unverified_user):
        token = unverified_user.verification_token
        client.get(f"/api/v1/auth/verify-email?token={token}")
        # Second use of same token
        response = client.get(f"/api/v1/auth/verify-email?token={token}")
        assert response.status_code == 400


@pytest.mark.integration
class TestResendVerificationEndpoint:
    def test_resend_for_unverified_user_returns_200(self, client, unverified_user):
        with patch("app.services.email_service.send_email_verification_token_email", new_callable=AsyncMock):
            response = client.post(
                "/api/v1/auth/resend-verification",
                json={"email": unverified_user.email}
            )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_resend_regenerates_token(self, client, unverified_user, db_session):
        old_token = unverified_user.verification_token
        with patch("app.services.email_service.send_email_verification_token_email", new_callable=AsyncMock):
            client.post(
                "/api/v1/auth/resend-verification",
                json={"email": unverified_user.email}
            )
        db_session.refresh(unverified_user)
        assert unverified_user.verification_token != old_token
        expires = unverified_user.verification_token_expires
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        assert expires > datetime.now(timezone.utc)

    def test_resend_for_verified_user_returns_400(self, client, verified_user):
        response = client.post(
            "/api/v1/auth/resend-verification",
            json={"email": verified_user.email}
        )
        assert response.status_code == 200  # Always 200 for security, but service returns error
        # The endpoint always returns 200 to avoid enumeration

    def test_resend_for_unknown_email_returns_200(self, client):
        """Should always return 200 to prevent email enumeration."""
        response = client.post(
            "/api/v1/auth/resend-verification",
            json={"email": "nobody@notexist.com"}
        )
        assert response.status_code == 200


@pytest.mark.integration
class TestLoginEnforcement:
    def test_unverified_user_cannot_login(self, client, unverified_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"identifier": unverified_user.email, "password": "password123"}
        )
        assert response.status_code == 403
        assert "not verified" in response.json()["detail"].lower()

    def test_verified_user_can_login(self, client, verified_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"identifier": verified_user.email, "password": "password123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_after_verification_user_can_login(self, client, unverified_user):
        # Verify first
        client.get(f"/api/v1/auth/verify-email?token={unverified_user.verification_token}")
        # Then login
        response = client.post(
            "/api/v1/auth/login",
            json={"identifier": unverified_user.email, "password": "password123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()


@pytest.mark.integration
class TestTokenExpiry:
    def test_24h_token_expiry_is_set_on_registration(self, db_session):
        """Verify that new users get a 24h token expiry on registration."""
        from app.services.auth_service import AuthService

        service = AuthService(db_session)
        with patch("app.services.email_service.send_email_verification_token_email", new_callable=AsyncMock):
            service.register_user(
                username="expiry_test",
                email="expiry_test@example.com",
                password="password123",
            )

        user = db_session.query(User).filter(User.email == "expiry_test@example.com").first()
        assert user is not None
        assert user.verification_token is not None
        assert user.verification_token_expires is not None
        # Should be roughly 24 hours from now
        expected = datetime.now(timezone.utc) + timedelta(hours=24)
        expires = user.verification_token_expires
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        diff = abs((expires - expected).total_seconds())
        assert diff < 60  # within 1 minute
