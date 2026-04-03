"""
Authentication service for handling user registration, login, and token management.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, UploadFile,Request
from ..models.user import User, UserProfile
from ..models.token_blacklist import TokenBlacklist
from app.config.settings import settings
import secrets
import logging
from app.schemas.auth import UserUpdateRequest
import os
from uuid import uuid4
from app.utils.security import get_password_hash


logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory rate limit stores: email → list of UTC datetimes
_password_reset_timestamps: dict = {}
_resend_verification_timestamps: dict = {}


def _check_rate_limit(store: dict, key: str, max_requests: int = 3, window_minutes: int = 60) -> bool:
    """Return True if the key is within the allowed rate, False if exceeded."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=window_minutes)
    timestamps = [t for t in store.get(key, []) if t > cutoff]
    if len(timestamps) >= max_requests:
        store[key] = timestamps
        return False
    timestamps.append(now)
    store[key] = timestamps
    return True

# JWT settings
SECRET_KEY = settings.JWT_SECRET
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)

    def create_access_token(self, user: User) -> str:
        """Create JWT access token."""
        jti = secrets.token_urlsafe(32)  # JWT ID for blacklisting
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
    "sub": str(user.id),
    "is_admin": user.is_admin,
    "exp": expire,
    "type": "access",
    "jti": jti
}

        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token."""
        jti = secrets.token_urlsafe(32)  # JWT ID for blacklisting
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh",
            "jti": jti
        }
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token."""
        if not token:
            logger.warning("Cannot decode empty token")
            return None
            
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError as e:
            if "expired" in str(e):
                logger.warning("Token has expired")
            elif "invalid" in str(e):
                logger.warning(f"Invalid token: {str(e)}")
            else:
                logger.error(f"JWT decode error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error decoding token: {str(e)}", exc_info=True)
            return None

    def register_user(
    self,
    username: str,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    is_email_verified: bool = False,
    is_phone_verified: bool = False,
    background_tasks: Optional[Any] = None,
    frontend_url: str = ""
) -> Dict[str, str]:
     """Register a new user."""

     if self.db.query(User).filter(User.email == email).first():
        raise ValueError("Email already registered")

     if phone_number and self.db.query(User).filter(User.phone_number == phone_number).first():
        raise ValueError("Phone number already registered")

     verification_token = secrets.token_urlsafe(32)
     verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)

     user = User()
     user.email = email
     user.password_hash = self.get_password_hash(password)
     user.name = full_name or username
     user.username = username
     user.phone_number = phone_number
     user.is_email_verified = is_email_verified
     user.is_phone_verified = is_phone_verified
     user.verification_token = verification_token
     user.verification_token_expires = verification_expires

     self.db.add(user)
     self.db.flush()

    # Create user profile
     profile = UserProfile(user_id=user.id, languages=[])
     profile.user = user
     profile.email = email
     profile.name = full_name or username
     profile.username = username
     if phone_number:
        profile.phone_number = phone_number

     self.db.add(profile)

     try:
        self.db.commit()
        self.db.refresh(user)
     except Exception as e:
        self.db.rollback()
        logger.error(f"Error registering user: {str(e)}")
        raise ValueError("Could not register user")

     # Send verification email if not already verified
     if not is_email_verified and frontend_url:
        from app.services.email_service import send_email_verification_token_email
        verify_url = f"{frontend_url}/auth/verify-email?token={verification_token}"
        if background_tasks:
            background_tasks.add_task(send_email_verification_token_email, email, verify_url)
        else:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(send_email_verification_token_email(email, verify_url))
                else:
                    loop.run_until_complete(send_email_verification_token_email(email, verify_url))
            except Exception as e:
                logger.error(f"Failed to send verification email: {e}")

     return {"user_id": str(user.id)}

    def authenticate_user(self, identifier: str, password: str) -> Dict[str, Any]:
      """Authenticate a user by email or phone number"""
      user = self.db.query(User).filter(
        (User.email == identifier) | (User.phone_number == identifier)
    ).first()

      if not user or not self.verify_password(password, str(user.password_hash)):
        return {"success": False, "reason": "invalid_credentials"}

      if not user.is_email_verified:
        return {"success": False, "reason": "email_not_verified"}

      user.last_login = datetime.now(timezone.utc)
      self.db.commit()

      access_token = self.create_access_token(user)
      refresh_token = self.create_refresh_token(str(user.id))

      return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
        "user_id": str(user.id)
    }

    def verify_email(self, token: str) -> Dict[str, Any]:
        """Verify user's email using verification token."""
        user = self.db.query(User).filter(User.verification_token == token).first()
        if not user:
            return {"success": False, "message": "Invalid verification token"}

        expires = getattr(user, 'verification_token_expires', None)
        if expires is not None:
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires:
                return {"success": False, "message": "Verification token has expired. Please request a new one."}

        user.is_email_verified = True
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        self.db.commit()

        # Complete any pending referral for this user
        try:
            from app.services.referral_service import ReferralService
            ReferralService(self.db).complete_referral(str(user.id))
        except Exception as exc:
            logger.warning("referral completion failed for user %s: %s", user.id, exc)

        return {
            "success": True,
            "message": "Email verified successfully",
            "user_id": str(user.id)
        }

    def resend_verification_email(
        self, email: str, background_tasks: Optional[Any] = None, frontend_url: str = ""
    ) -> Dict[str, Any]:
        """Regenerate verification token and resend verification email."""
        if not _check_rate_limit(_resend_verification_timestamps, email.lower()):
            raise ValueError("Too many verification email requests. Please wait before trying again.")

        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # Silent response to avoid email enumeration
            return {"success": True, "message": "If that email is registered, a verification email has been sent"}

        if user.is_email_verified:
            return {"success": False, "message": "Email is already verified"}

        verification_token = secrets.token_urlsafe(32)
        verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
        user.verification_token = verification_token
        user.verification_token_expires = verification_expires
        self.db.commit()

        if frontend_url:
            from app.services.email_service import send_email_verification_token_email
            verify_url = f"{frontend_url}/auth/verify-email?token={verification_token}"
            if background_tasks:
                background_tasks.add_task(send_email_verification_token_email, email, verify_url)
            else:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(send_email_verification_token_email(email, verify_url))
                    else:
                        loop.run_until_complete(send_email_verification_token_email(email, verify_url))
                except Exception as e:
                    logger.error(f"Failed to resend verification email: {e}")

        return {"success": True, "message": "If that email is registered, a verification email has been sent"}

    def request_password_reset(self, email: str) -> Optional[str]:
        """Generate password reset token with 15-minute TTL."""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None

        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(minutes=15)
        setattr(user, 'reset_password_token', token)
        setattr(user, 'reset_password_token_expires', expires)
        self.db.commit()
        return token

    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """Reset user's password using reset token. Token is single-use."""
        user = self.db.query(User).filter(User.reset_password_token == token).first()
        if not user:
            return {"success": False, "message": "Invalid or expired reset token"}

        expires = getattr(user, 'reset_password_token_expires', None)
        now = datetime.now(timezone.utc)
        if expires is not None and expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires is None or now > expires:
            setattr(user, 'reset_password_token', None)
            setattr(user, 'reset_password_token_expires', None)
            self.db.commit()
            return {"success": False, "message": "Reset token has expired"}

        setattr(user, 'password_hash', self.get_password_hash(new_password))
        # Single-use: clear token immediately after successful reset
        setattr(user, 'reset_password_token', None)
        setattr(user, 'reset_password_token_expires', None)
        self.db.commit()

        return {"success": True, "message": "Password reset successfully"}

    def create_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> UserProfile:
        """Create or update user profile with detailed information"""
        # Check if profile exists
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if profile:
            # Update existing profile
            for key, value in profile_data.items():
                setattr(profile, key, value)
        else:
            # Create new profile
            profile = UserProfile()
            setattr(profile, 'user_id', user_id)
            for key, value in profile_data.items():
                setattr(profile, key, value)
            self.db.add(profile)
        
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def verify_credentials(self, email: str, password: str) -> Optional[User]:
        """Verify user credentials"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("User not found")

        # Get password hash safely
        password_hash = getattr(user, 'password_hash', None)
        if not password_hash:
            raise ValueError("Invalid password")

        # Convert to string and verify
        if not self.verify_password(password, str(password_hash)):
            raise ValueError("Invalid password")

        return user

    def store_ai_analysis(self, user_id: str, analysis: Dict[str, Any]) -> None:
        """Store AI's analysis of user profile"""
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise ValueError("User profile not found")

        setattr(profile, 'ai_analysis', analysis)
        self.db.commit()

    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted."""
        try:
            blacklisted_token = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.token_jti == jti
            ).first()
            return blacklisted_token is not None
        except Exception as e:
            logger.error(f"Error checking token blacklist: {str(e)}")
            return False

    def get_current_user(self, token: Optional[str] = None) -> Optional[User]:
        """Get the current user from a token."""
        if not token:
            logger.warning("Token is empty")
            return None
            
        try:
            # Remove "Bearer " prefix if present
            if token.startswith("Bearer "):
                token = token.replace("Bearer ", "")
            
            # Decode token to get user_id
            payload = self.decode_token(token)
            
            if not payload or "sub" not in payload:
                logger.warning("Invalid token payload")
                return None
            
            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and self.is_token_blacklisted(jti):
                logger.warning("Token is blacklisted")
                return None
                
            user_id = payload["sub"]
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                logger.warning(f"User not found for id: {user_id}")
                return None
                
            return user
            
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            return None

    def invalidate_token(self, token: str) -> bool:
        """Invalidate a token by adding it to the blacklist."""
        try:
            # Remove "Bearer " prefix if present
            if token.startswith("Bearer "):
                token = token.replace("Bearer ", "")
            
            # Decode token to get payload
            payload = self.decode_token(token)
            if not payload or "sub" not in payload or "jti" not in payload:
                return False
                
            user_id = payload["sub"]
            jti = payload["jti"]
            exp = payload.get("exp")
            
            # Convert exp timestamp to datetime
            expires_at = datetime.utcfromtimestamp(exp) if exp else datetime.now(timezone.utc) + timedelta(hours=1)
            
            # Add token to blacklist
            blacklisted_token = TokenBlacklist(
                token_jti=jti,
                user_id=user_id,
                expires_at=expires_at
            )
            
            self.db.add(blacklisted_token)
            self.db.commit()
            
            logger.info(f"Token {jti[:8]}... blacklisted for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating token: {str(e)}")
            return False

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        try:
            # Remove "Bearer " prefix if present
            if refresh_token.startswith("Bearer "):
                refresh_token = refresh_token.replace("Bearer ", "")
            
            # Decode refresh token
            payload = self.decode_token(refresh_token)
            if not payload or "sub" not in payload:
                return {"success": False, "message": "Invalid refresh token"}
            
            # Check if it's actually a refresh token
            if payload.get("type") != "refresh":
                return {"success": False, "message": "Invalid token type"}
            
            user_id = payload["sub"]
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return {"success": False, "message": "User not found"}
            
            # Create new access token
            new_access_token = self.create_access_token(user)
            
            return {
                "success": True,
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user_id": str(user.id)
            }
            
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return {"success": False, "message": "Token refresh failed"}

    def send_password_reset(
        self, email: str, background_tasks: Optional[Any] = None, base_url: str = ""
    ) -> Dict[str, Any]:
        """Send password reset email. Always returns success to avoid email enumeration."""
        _silent = {"success": True, "message": "If that email is registered, a reset link has been sent"}

        if not _check_rate_limit(_password_reset_timestamps, email.lower()):
            raise ValueError("Too many password reset requests. Please wait before trying again.")

        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return _silent

        from app.services.email_service import send_password_reset_email

        reset_token = self.request_password_reset(email)
        if not reset_token:
            return {"success": True, "message": "If that email is registered, a reset link has been sent"}

        reset_url = f"{base_url}/auth/reset-password?token={reset_token}"

        if background_tasks:
            background_tasks.add_task(send_password_reset_email, email, reset_url)
        else:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(send_password_reset_email(email, reset_url))
                else:
                    loop.run_until_complete(send_password_reset_email(email, reset_url))
            except Exception as e:
                logger.error(f"Failed to send password reset email: {e}")

        return {"success": True, "message": "If that email is registered, a reset link has been sent"}

    async def update_profile(
    self,
    user: User,
    username: Optional[str] = None,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    phone_number: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    file: Optional[UploadFile] = None,
    request: Optional[Request] = None
) -> User:

    #  Username check
     if username is not None:
        existing = (
            self.db.query(User)
            .filter(User.username == username, User.id != user.id)  # ignore self
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Username already in use")
        user.username = username

    #  Email check
     if email is not None:
        existing = (
            self.db.query(User)
            .filter(User.email == email, User.id != user.id)  # ignore self
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = email

    #  Phone number check
     if phone_number is not None:
        existing = (
            self.db.query(User)
            .filter(User.phone_number == phone_number, User.id != user.id)  # ignore self
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Phone number already in use")
        user.phone_number = phone_number

     if full_name is not None:
        user.name = full_name

     if not user.profile:
        user.profile = UserProfile(user_id=user.id)
        self.db.add(user.profile)

     if country is not None:
        user.country = country
     if city is not None:
        user.city = city

     try:
        self.db.commit()
        self.db.refresh(user)
     except IntegrityError:
        self.db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate field value detected")
     self.db.refresh(user, attribute_names=["profile"])
     return user