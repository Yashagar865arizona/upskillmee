"""Unit tests for ReferralService."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.services.referral_service import ReferralService, _generate_code
from app.models.user import User
from app.models.referral import Referral


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(user_id="user-1", referral_code=None):
    u = MagicMock(spec=User)
    u.id = user_id
    u.referral_code = referral_code
    return u


def _make_referral(**kwargs):
    defaults = dict(
        id="ref-1",
        referrer_user_id="user-1",
        referred_user_id="user-2",
        referral_code="ABCD1234",
        status="pending",
        reward_applied=False,
    )
    defaults.update(kwargs)
    r = MagicMock(spec=Referral)
    for k, v in defaults.items():
        setattr(r, k, v)
    return r


# ---------------------------------------------------------------------------
# _generate_code
# ---------------------------------------------------------------------------

def test_generate_code_length():
    code = _generate_code()
    assert len(code) == 8


def test_generate_code_unique():
    codes = {_generate_code() for _ in range(100)}
    # With 8 chars from 36-symbol alphabet the chance of collision is negligible
    assert len(codes) > 90


def test_generate_code_charset():
    for _ in range(20):
        code = _generate_code()
        assert code.isalnum()
        assert code == code.upper()


# ---------------------------------------------------------------------------
# ensure_referral_code
# ---------------------------------------------------------------------------

def test_ensure_referral_code_existing():
    db = MagicMock()
    service = ReferralService(db)
    user = _make_user(referral_code="EXISTING1")
    result = service.ensure_referral_code(user)
    assert result == "EXISTING1"
    db.commit.assert_not_called()


def test_ensure_referral_code_generates_new():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None  # no collision
    service = ReferralService(db)
    user = _make_user()
    user.referral_code = None
    result = service.ensure_referral_code(user)
    assert len(result) == 8
    db.commit.assert_called_once()


def test_ensure_referral_code_retries_on_collision():
    db = MagicMock()
    existing_user = MagicMock()
    # First query returns collision, second returns None
    db.query.return_value.filter.return_value.first.side_effect = [existing_user, None]
    service = ReferralService(db)
    user = _make_user()
    user.referral_code = None
    result = service.ensure_referral_code(user)
    assert result is not None


# ---------------------------------------------------------------------------
# get_user_by_referral_code
# ---------------------------------------------------------------------------

def test_get_user_by_referral_code_found():
    db = MagicMock()
    expected = _make_user("user-42", referral_code="CODE1234")
    db.query.return_value.filter.return_value.first.return_value = expected
    service = ReferralService(db)
    result = service.get_user_by_referral_code("CODE1234")
    assert result is expected


def test_get_user_by_referral_code_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    service = ReferralService(db)
    assert service.get_user_by_referral_code("BADCODE1") is None


# ---------------------------------------------------------------------------
# process_referral_signup
# ---------------------------------------------------------------------------

def test_process_referral_signup_valid():
    db = MagicMock()
    referrer = _make_user("referrer-1", referral_code="REF12345")

    def query_side_effect(model):
        q = MagicMock()
        if model is User:
            q.filter.return_value.first.return_value = referrer
        else:  # Referral
            q.filter.return_value.first.return_value = None  # no existing referral
        return q

    db.query.side_effect = query_side_effect
    service = ReferralService(db)
    result = service.process_referral_signup("referred-2", "REF12345")
    assert result is True
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_process_referral_signup_unknown_code():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    service = ReferralService(db)
    result = service.process_referral_signup("referred-2", "UNKNOWN1")
    assert result is False
    db.add.assert_not_called()


def test_process_referral_signup_self_referral():
    db = MagicMock()
    referrer = _make_user("same-user", referral_code="SELF1234")
    db.query.return_value.filter.return_value.first.return_value = referrer
    service = ReferralService(db)
    result = service.process_referral_signup("same-user", "SELF1234")
    assert result is False
    db.add.assert_not_called()


def test_process_referral_signup_duplicate_idempotent():
    db = MagicMock()
    referrer = _make_user("referrer-1", referral_code="REF12345")
    existing_referral = _make_referral()

    def query_side_effect(model):
        q = MagicMock()
        if model is User:
            q.filter.return_value.first.return_value = referrer
        else:
            q.filter.return_value.first.return_value = existing_referral
        return q

    db.query.side_effect = query_side_effect
    service = ReferralService(db)
    result = service.process_referral_signup("referred-2", "REF12345")
    assert result is True
    db.add.assert_not_called()


# ---------------------------------------------------------------------------
# complete_referral
# ---------------------------------------------------------------------------

def test_complete_referral_success():
    db = MagicMock()
    referral = _make_referral(status="pending", reward_applied=False)
    db.query.return_value.filter.return_value.first.return_value = referral
    service = ReferralService(db)
    result = service.complete_referral("referred-2")
    assert result is True
    assert referral.status == "completed"
    assert referral.reward_applied is True
    assert referral.completed_at is not None
    db.commit.assert_called_once()


def test_complete_referral_no_pending():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    service = ReferralService(db)
    result = service.complete_referral("no-referral-user")
    assert result is False
    db.commit.assert_not_called()


# ---------------------------------------------------------------------------
# get_referral_stats
# ---------------------------------------------------------------------------

def test_get_referral_stats_user_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    service = ReferralService(db)
    with pytest.raises(ValueError, match="User not found"):
        service.get_referral_stats("ghost-user")


def test_get_referral_stats_counts():
    db = MagicMock()
    user = _make_user("referrer-1", referral_code="CODE1234")

    completed = _make_referral(status="completed", reward_applied=True)
    pending = _make_referral(status="pending", reward_applied=False)

    def query_side_effect(model):
        q = MagicMock()
        if model is User:
            q.filter.return_value.first.return_value = user
        else:  # Referral
            q.filter.return_value.all.return_value = [completed, pending]
        return q

    db.query.side_effect = query_side_effect
    service = ReferralService(db)
    stats = service.get_referral_stats("referrer-1")

    assert stats["referral_code"] == "CODE1234"
    assert stats["total_referrals"] == 2
    assert stats["completed_referrals"] == 1
    assert stats["pending_referrals"] == 1
    assert stats["rewards_earned"] == 1


def test_get_referral_stats_empty():
    db = MagicMock()
    user = _make_user("referrer-1", referral_code="CODE1234")

    def query_side_effect(model):
        q = MagicMock()
        if model is User:
            q.filter.return_value.first.return_value = user
        else:
            q.filter.return_value.all.return_value = []
        return q

    db.query.side_effect = query_side_effect
    service = ReferralService(db)
    stats = service.get_referral_stats("referrer-1")

    assert stats["total_referrals"] == 0
    assert stats["completed_referrals"] == 0
    assert stats["rewards_earned"] == 0
