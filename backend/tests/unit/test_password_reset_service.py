"""
Unit tests for email-based password reset service logic.

These tests are fully isolated — no database connections required.
We test AuthService methods directly using MagicMock sessions and
patched model/settings imports.
"""

import sys
import types
import secrets
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, AsyncMock


# ---------------------------------------------------------------------------
# Bootstrap: stub out modules that try to connect to the DB on import
# so these tests work without a running database / asyncpg driver.
# ---------------------------------------------------------------------------

def _make_stub_module(name):
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


# Stub fastapi_mail before any app module is imported
_fm_mod = _make_stub_module("fastapi_mail")
_fm_mod.ConnectionConfig = MagicMock()
_fm_mod.FastMail = MagicMock()
_fm_mod.MessageSchema = MagicMock()
_fm_mod.MessageType = MagicMock()

# Stub settings before any app module is imported
_settings_mod = _make_stub_module("app.config.settings")
_fake_settings = MagicMock()
_fake_settings.DATABASE_URL = "sqlite:///./test.db"
_fake_settings.JWT_SECRET = "test-secret"
_fake_settings.JWT_ALGORITHM = "HS256"
_fake_settings.WEBSITE_URL = "http://localhost:3000"
_fake_settings.ENVIRONMENT = "test"
_settings_mod.settings = _fake_settings

_make_stub_module("app.config")
sys.modules["app.config"].settings = _fake_settings

# Stub the async engine so session.py doesn't fail on import
import sqlalchemy.ext.asyncio as _sqla_async  # noqa: E402
_real_create_async = _sqla_async.create_async_engine

def _noop_create_async_engine(*args, **kwargs):
    return MagicMock()

_sqla_async.create_async_engine = _noop_create_async_engine

# Now import the service under test
from app.services.auth_service import AuthService  # noqa: E402

# Restore async engine (good practice)
_sqla_async.create_async_engine = _real_create_async


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(user=None):
    """Return a minimal mock SQLAlchemy session."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user
    return db


def _make_user(email="user@example.com", token=None, expires=None):
    """Build a simple User-like namespace (no ORM needed)."""
    from types import SimpleNamespace
    u = SimpleNamespace(
        email=email,
        reset_password_token=token,
        reset_password_token_expires=expires,
        password_hash="$2b$12$hashed",
    )
    return u


def _svc(user=None):
    """Create AuthService with a mock DB that returns `user` for filter queries."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user
    return AuthService(db), db


# ---------------------------------------------------------------------------
# request_password_reset
# ---------------------------------------------------------------------------

class TestRequestPasswordReset:

    def test_unknown_email_returns_none(self):
        svc, db = _svc(user=None)
        result = svc.request_password_reset("nobody@unknown.com")
        assert result is None
        db.commit.assert_not_called()

    def test_known_email_returns_token(self):
        user = _make_user()
        svc, db = _svc(user=user)
        token = svc.request_password_reset(user.email)
        assert isinstance(token, str) and len(token) > 20
        db.commit.assert_called_once()

    def test_token_expiry_is_approximately_15_minutes(self):
        user = _make_user()
        svc, _ = _svc(user=user)
        before = datetime.now(timezone.utc)
        svc.request_password_reset(user.email)
        after = datetime.now(timezone.utc)

        assert user.reset_password_token_expires is not None
        expires = user.reset_password_token_expires
        assert before + timedelta(minutes=14) < expires < after + timedelta(minutes=16)

    def test_token_stored_on_user(self):
        user = _make_user()
        svc, _ = _svc(user=user)
        token = svc.request_password_reset(user.email)
        assert user.reset_password_token == token


# ---------------------------------------------------------------------------
# reset_password
# ---------------------------------------------------------------------------

class TestResetPassword:

    def test_valid_token_returns_success(self):
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(minutes=10)
        user = _make_user(token=token, expires=expires)
        svc, _ = _svc(user=user)
        with patch.object(svc, "get_password_hash", return_value="$hashed"):
            result = svc.reset_password(token, "NewPass1!")
        assert result["success"] is True

    def test_valid_token_clears_after_use(self):
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(minutes=10)
        user = _make_user(token=token, expires=expires)
        svc, db = _svc(user=user)
        with patch.object(svc, "get_password_hash", return_value="$hashed"):
            svc.reset_password(token, "NewPass1!")
        assert user.reset_password_token is None
        assert user.reset_password_token_expires is None
        db.commit.assert_called()

    def test_invalid_token_returns_failure(self):
        svc, _ = _svc(user=None)
        result = svc.reset_password("bad-token-xyz", "anything")
        assert result["success"] is False

    def test_expired_token_returns_failure(self):
        token = secrets.token_urlsafe(32)
        expired = datetime.now(timezone.utc) - timedelta(minutes=1)
        user = _make_user(token=token, expires=expired)
        svc, _ = _svc(user=user)
        result = svc.reset_password(token, "NewPass1!")
        assert result["success"] is False
        assert "expired" in result["message"].lower()

    def test_expired_token_clears_stored_token(self):
        token = secrets.token_urlsafe(32)
        expired = datetime.now(timezone.utc) - timedelta(seconds=30)
        user = _make_user(token=token, expires=expired)
        svc, db = _svc(user=user)
        svc.reset_password(token, "anything")
        assert user.reset_password_token is None
        db.commit.assert_called()

    def test_none_expiry_treated_as_expired(self):
        """Token row without expiry (old row, no TTL) must be rejected."""
        token = secrets.token_urlsafe(32)
        user = _make_user(token=token, expires=None)
        svc, _ = _svc(user=user)
        result = svc.reset_password(token, "NewPass1!")
        assert result["success"] is False

    def test_second_use_of_same_token_fails(self):
        """After first successful reset, token is cleared → second use fails."""
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(minutes=10)
        user = _make_user(token=token, expires=expires)

        # First use
        svc1, _ = _svc(user=user)
        with patch.object(svc1, "get_password_hash", return_value="$hashed"):
            r1 = svc1.reset_password(token, "FirstReset!")
        assert r1["success"] is True

        # Token is now cleared on the user object
        # Second attempt: query returns None (token was cleared/not found)
        svc2, _ = _svc(user=None)
        r2 = svc2.reset_password(token, "SecondReset!")
        assert r2["success"] is False


# ---------------------------------------------------------------------------
# send_password_reset (silent success / no email enumeration)
# ---------------------------------------------------------------------------

class TestSendPasswordReset:

    def test_unknown_email_returns_success_silently(self):
        svc, db = _svc(user=None)
        result = svc.send_password_reset("ghost@example.com")
        assert result["success"] is True
        # Must not expose that email doesn't exist
        assert "registered" in result["message"].lower() or "link" in result["message"].lower()

    def test_known_email_returns_success(self):
        user = _make_user()
        svc, _ = _svc(user=user)
        with patch("app.services.auth_service.AuthService.request_password_reset", return_value="tok"):
            result = svc.send_password_reset(user.email, base_url="http://localhost:3000")
        assert result["success"] is True
