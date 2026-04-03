from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from uuid import uuid4
from .base_model import BaseModel
from ..database.base import Base


class Referral(BaseModel, Base):
    """
    Tracks referral relationships between users.
    status: 'pending' = referred user signed up but hasn't verified email
            'completed' = referred user verified email; reward may be applied
    """
    __tablename__ = "referrals"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    referrer_user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    referred_user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    referral_code = Column(String, nullable=False)
    status = Column(String, default="pending")   # pending | completed
    reward_applied = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    referrer = relationship("User", foreign_keys=[referrer_user_id], backref="referrals_made")
    referred = relationship("User", foreign_keys=[referred_user_id], backref="referred_by")
