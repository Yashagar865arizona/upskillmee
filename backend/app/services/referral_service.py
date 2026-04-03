"""
Referral service — manages referral codes, tracking, and reward records.
Reward logic is record-keeping only (no payment integration).
"""
import secrets
import string
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models.user import User
from ..models.referral import Referral

logger = logging.getLogger(__name__)

_CODE_ALPHABET = string.ascii_uppercase + string.digits
_CODE_LENGTH = 8


def _generate_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))


class ReferralService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Referral code management
    # ------------------------------------------------------------------

    def ensure_referral_code(self, user: User) -> str:
        """Return existing referral code or generate and persist a new one."""
        if user.referral_code:
            return user.referral_code
        for _ in range(10):
            code = _generate_code()
            if not self.db.query(User).filter(User.referral_code == code).first():
                user.referral_code = code
                self.db.commit()
                self.db.refresh(user)
                return code
        raise RuntimeError("Could not generate unique referral code")

    def get_user_by_referral_code(self, code: str) -> Optional[User]:
        return self.db.query(User).filter(User.referral_code == code).first()

    # ------------------------------------------------------------------
    # Signup hook
    # ------------------------------------------------------------------

    def process_referral_signup(self, referred_user_id: str, referral_code: str) -> bool:
        """
        Called right after a referred user is created.
        Creates a pending Referral row.
        Returns True if the referral was recorded, False if invalid.
        """
        referrer = self.get_user_by_referral_code(referral_code)
        if not referrer:
            logger.warning("process_referral_signup: unknown code %s", referral_code)
            return False
        if str(referrer.id) == referred_user_id:
            return False  # self-referral guard

        # Idempotency: ignore if already tracked
        existing = (
            self.db.query(Referral)
            .filter(Referral.referred_user_id == referred_user_id)
            .first()
        )
        if existing:
            return True

        referral = Referral(
            referrer_user_id=str(referrer.id),
            referred_user_id=referred_user_id,
            referral_code=referral_code,
            status="pending",
        )
        self.db.add(referral)
        self.db.commit()
        logger.info(
            "Referral recorded: referrer=%s referred=%s",
            referrer.id, referred_user_id,
        )
        return True

    # ------------------------------------------------------------------
    # Email-verification hook
    # ------------------------------------------------------------------

    def complete_referral(self, referred_user_id: str) -> bool:
        """
        Called when a referred user verifies their email.
        Marks the referral as completed and records the reward.
        """
        referral = (
            self.db.query(Referral)
            .filter(
                Referral.referred_user_id == referred_user_id,
                Referral.status == "pending",
            )
            .first()
        )
        if not referral:
            return False

        referral.status = "completed"
        referral.reward_applied = True
        referral.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        logger.info(
            "Referral completed: id=%s referrer=%s",
            referral.id, referral.referrer_user_id,
        )
        return True

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_referral_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Returns referral code + stats for a given user.
        Generates a code if the user doesn't have one yet.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        code = self.ensure_referral_code(user)

        referrals = (
            self.db.query(Referral)
            .filter(Referral.referrer_user_id == user_id)
            .all()
        )
        total = len(referrals)
        completed = sum(1 for r in referrals if r.status == "completed")
        pending = total - completed
        rewards_earned = sum(1 for r in referrals if r.reward_applied)

        return {
            "referral_code": code,
            "total_referrals": total,
            "completed_referrals": completed,
            "pending_referrals": pending,
            "rewards_earned": rewards_earned,
            "reward_description": "1 free month of Pro per successful referral",
        }
