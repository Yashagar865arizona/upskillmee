"""
Unit tests for AuthService.
Tests authentication, registration, token management, and user verification.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from jose import jwt
import secrets

from app.services.auth_service import AuthService
from app.models.user import User, UserProfile
from app.models.token_blacklist import TokenBlacklist


class TestAuthService:
    """Test suite for AuthService."""

    def test_verify_password_success(self, auth_service):
        """Test successful password verification."""
        plain_password = "test_password_123"
        hashed_password = auth_service.get_password_hash(plain_password)
        
        result = auth_service.verify_password(plain_password, hashed_password)
        assert result is True

    def test_verify_password_failure(self, auth_service):
        """Test failed password verification."""
        plain_password = "test_password_123"
        wrong_password = "wrong_password"
        hashed_password = auth_service.get_password_hash(plain_password)
        
        result = auth_service.verify_password(wrong_password, hashed_password)
        assert result is False

    def test_get_password_hash(self, auth_service):
        """Test password hashing."""
        password = "test_password_123"
        hashed = auth_service.get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are typically 60 characters
        assert hashed.startswith("$2b$")

    def test_create_access_token_with_user_id(self, auth_service):
        """Test access token creation with user ID."""
        user_id = "test-user-123"
        token = auth_service.create_access_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are typically long
        
        # Decode and verify token content
        from app.config.settings import settings
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "jti" in payload

    def test_create_access_token_with_dict(self, auth_service):
        """Test access token creation with dictionary data."""
        data = {"sub": "test-user-123", "role": "user"}
        token = auth_service.create_access_token(data)
        
        assert isinstance(token, str)
        
        # Decode and verify token content
        from app.config.settings import settings
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == "test-user-123"
        assert payload["role"] == "user"
        assert payload["type"] == "access"

    def test_create_refresh_token(self, auth_service):
        """Test refresh token creation."""
        user_id = "test-user-123"
        token = auth_service.create_refresh_token(user_id)
        
        assert isinstance(token, str)
        
        # Decode and verify token content
        from app.config.settings import settings
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "jti" in payload

    def test_decode_token_success(self, auth_service):
        """Test successful token decoding."""
        user_id = "test-user-123"
        token = auth_service.create_access_token(user_id)
        
        payload = auth_service.decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_decode_token_invalid(self, auth_service):
        """Test decoding invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = auth_service.decode_token(invalid_token)
        
        assert payload is None

    def test_decode_token_empty(self, auth_service):
        """Test decoding empty token."""
        payload = auth_service.decode_token("")
        assert payload is None
        
        payload = auth_service.decode_token(None)
        assert payload is None

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, test_db_session):
        """Test successful user registration."""
        username = "testuser"
        email = "newuser@example.com"
        password = "secure_password_123"
        full_name = "Test User"
        
        result = await auth_service.register_user(username, email, password, full_name)
        
        assert "user_id" in result
        assert isinstance(result["user_id"], str)
        
        # Verify user was created in database
        user = test_db_session.query(User).filter(User.email == email).first()
        assert user is not None
        assert user.email == email
        assert user.name == full_name
        assert auth_service.verify_password(password, str(user.password_hash))

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, auth_service, test_user):
        """Test registration with duplicate email."""
        username = "testuser2"
        email = test_user.email  # Use existing user's email
        password = "secure_password_123"
        
        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.register_user(username, email, password)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, test_user):
        """Test successful user authentication."""
        # Set a known password for the test user
        password = "test_password_123"
        test_user.password_hash = auth_service.get_password_hash(password)
        auth_service.db.commit()
        
        result = await auth_service.authenticate_user(test_user.email, password)
        
        assert result["success"] is True
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        assert result["user_id"] == str(test_user.id)
        assert isinstance(result["expires_in"], int)

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service, test_user):
        """Test authentication with wrong password."""
        result = await auth_service.authenticate_user(test_user.email, "wrong_password")
        
        assert result["success"] is False
        assert "access_token" not in result

    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent(self, auth_service):
        """Test authentication with non-existent user."""
        result = await auth_service.authenticate_user("nonexistent@example.com", "password")
        
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_verify_email_success(self, auth_service, test_user):
        """Test successful email verification."""
        # Set verification token for test user
        verification_token = "test_verification_token"
        test_user.verification_token = verification_token
        test_user.is_verified = False
        auth_service.db.commit()
        
        result = await auth_service.verify_email(verification_token)
        
        assert result["success"] is True
        assert result["user_id"] == str(test_user.id)
        
        # Verify user is now verified
        auth_service.db.refresh(test_user)
        assert test_user.is_verified is True
        assert test_user.verification_token is None

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, auth_service):
        """Test email verification with invalid token."""
        result = await auth_service.verify_email("invalid_token")
        
        assert result["success"] is False
        assert "Invalid verification token" in result["message"]

    @pytest.mark.asyncio
    async def test_request_password_reset_success(self, auth_service, test_user):
        """Test successful password reset request."""
        reset_token = await auth_service.request_password_reset(test_user.email)
        
        assert reset_token is not None
        assert isinstance(reset_token, str)
        assert len(reset_token) > 20  # Should be a secure token
        
        # Verify token was saved to user
        auth_service.db.refresh(test_user)
        assert test_user.reset_password_token == reset_token

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_user(self, auth_service):
        """Test password reset request for non-existent user."""
        reset_token = await auth_service.request_password_reset("nonexistent@example.com")
        
        assert reset_token is None

    @pytest.mark.asyncio
    async def test_reset_password_success(self, auth_service, test_user):
        """Test successful password reset."""
        # Set reset token for test user
        reset_token = "test_reset_token"
        test_user.reset_password_token = reset_token
        auth_service.db.commit()
        
        new_password = "new_secure_password_123"
        result = await auth_service.reset_password(reset_token, new_password)
        
        assert result["success"] is True
        assert "Password reset successfully" in result["message"]
        
        # Verify password was changed and token was cleared
        auth_service.db.refresh(test_user)
        assert auth_service.verify_password(new_password, str(test_user.password_hash))
        assert test_user.reset_password_token is None

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, auth_service):
        """Test password reset with invalid token."""
        result = await auth_service.reset_password("invalid_token", "new_password")
        
        assert result["success"] is False
        assert "Invalid reset token" in result["message"]

    def test_is_token_blacklisted_false(self, auth_service):
        """Test checking non-blacklisted token."""
        jti = "test_jti_123"
        
        result = auth_service.is_token_blacklisted(jti)
        
        assert result is False

    def test_is_token_blacklisted_true(self, auth_service, test_db_session):
        """Test checking blacklisted token."""
        jti = "blacklisted_jti_123"
        
        # Add token to blacklist
        blacklisted_token = TokenBlacklist(
            token_jti=jti,
            user_id="test-user-123",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        test_db_session.add(blacklisted_token)
        test_db_session.commit()
        
        result = auth_service.is_token_blacklisted(jti)
        
        assert result is True

    def test_get_current_user_success(self, auth_service, test_user):
        """Test getting current user from valid token."""
        token = auth_service.create_access_token(str(test_user.id))
        
        user = auth_service.get_current_user(token)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_get_current_user_with_bearer_prefix(self, auth_service, test_user):
        """Test getting current user from token with Bearer prefix."""
        token = auth_service.create_access_token(str(test_user.id))
        bearer_token = f"Bearer {token}"
        
        user = auth_service.get_current_user(bearer_token)
        
        assert user is not None
        assert user.id == test_user.id

    def test_get_current_user_invalid_token(self, auth_service):
        """Test getting current user with invalid token."""
        user = auth_service.get_current_user("invalid_token")
        
        assert user is None

    def test_get_current_user_empty_token(self, auth_service):
        """Test getting current user with empty token."""
        user = auth_service.get_current_user("")
        assert user is None
        
        user = auth_service.get_current_user(None)
        assert user is None

    def test_get_current_user_blacklisted_token(self, auth_service, test_user, test_db_session):
        """Test getting current user with blacklisted token."""
        token = auth_service.create_access_token(str(test_user.id))
        
        # Decode token to get JTI
        from app.config.settings import settings
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        jti = payload["jti"]
        
        # Blacklist the token
        blacklisted_token = TokenBlacklist(
            token_jti=jti,
            user_id=str(test_user.id),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        test_db_session.add(blacklisted_token)
        test_db_session.commit()
        
        user = auth_service.get_current_user(token)
        
        assert user is None

    @pytest.mark.asyncio
    async def test_invalidate_token_success(self, auth_service, test_user):
        """Test successful token invalidation."""
        token = auth_service.create_access_token(str(test_user.id))
        
        result = await auth_service.invalidate_token(token)
        
        assert result is True
        
        # Verify token is now blacklisted
        from app.config.settings import settings
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        jti = payload["jti"]
        
        assert auth_service.is_token_blacklisted(jti) is True

    @pytest.mark.asyncio
    async def test_invalidate_token_with_bearer_prefix(self, auth_service, test_user):
        """Test token invalidation with Bearer prefix."""
        token = auth_service.create_access_token(str(test_user.id))
        bearer_token = f"Bearer {token}"
        
        result = await auth_service.invalidate_token(bearer_token)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_invalidate_token_invalid(self, auth_service):
        """Test invalidating invalid token."""
        result = await auth_service.invalidate_token("invalid_token")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, auth_service, test_user):
        """Test successful access token refresh."""
        refresh_token = auth_service.create_refresh_token(str(test_user.id))
        
        result = await auth_service.refresh_access_token(refresh_token)
        
        assert result["success"] is True
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert result["user_id"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid(self, auth_service):
        """Test refresh with invalid token."""
        result = await auth_service.refresh_access_token("invalid_token")
        
        assert result["success"] is False
        assert "Invalid refresh token" in result["message"]

    @pytest.mark.asyncio
    async def test_refresh_access_token_wrong_type(self, auth_service, test_user):
        """Test refresh with access token instead of refresh token."""
        access_token = auth_service.create_access_token(str(test_user.id))
        
        result = await auth_service.refresh_access_token(access_token)
        
        assert result["success"] is False
        assert "Invalid token type" in result["message"]

    @pytest.mark.asyncio
    async def test_create_user_profile_new(self, auth_service, test_user):
        """Test creating new user profile."""
        profile_data = {
            "learning_style": "visual",
            "career_goals": ["data scientist"],
            "skill_levels": {"python": "intermediate"},
            "interests": ["machine learning", "statistics"]
        }
        
        profile = await auth_service.create_user_profile(str(test_user.id), profile_data)
        
        assert profile is not None
        assert profile.user_id == str(test_user.id)
        assert profile.learning_style == "visual"
        assert profile.career_goals == ["data scientist"]

    @pytest.mark.asyncio
    async def test_create_user_profile_update_existing(self, auth_service, test_user_profile):
        """Test updating existing user profile."""
        new_data = {
            "learning_style": "kinesthetic",
            "interests": ["robotics", "IoT"]
        }
        
        profile = await auth_service.create_user_profile(str(test_user_profile.user_id), new_data)
        
        assert profile is not None
        assert profile.learning_style == "kinesthetic"
        assert profile.interests == ["robotics", "IoT"]

    @pytest.mark.asyncio
    async def test_verify_credentials_success(self, auth_service, test_user):
        """Test successful credential verification."""
        password = "test_password_123"
        test_user.password_hash = auth_service.get_password_hash(password)
        auth_service.db.commit()
        
        user = await auth_service.verify_credentials(test_user.email, password)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_verify_credentials_user_not_found(self, auth_service):
        """Test credential verification with non-existent user."""
        with pytest.raises(ValueError, match="User not found"):
            await auth_service.verify_credentials("nonexistent@example.com", "password")

    @pytest.mark.asyncio
    async def test_verify_credentials_wrong_password(self, auth_service, test_user):
        """Test credential verification with wrong password."""
        password = "correct_password"
        test_user.password_hash = auth_service.get_password_hash(password)
        auth_service.db.commit()
        
        with pytest.raises(ValueError, match="Invalid password"):
            await auth_service.verify_credentials(test_user.email, "wrong_password")

    @pytest.mark.asyncio
    async def test_store_ai_analysis_success(self, auth_service, test_user_profile):
        """Test storing AI analysis in user profile."""
        analysis = {
            "personality_type": "analytical",
            "learning_preferences": ["structured", "project-based"],
            "recommended_pace": "moderate"
        }
        
        await auth_service.store_ai_analysis(str(test_user_profile.user_id), analysis)
        
        # Verify analysis was stored
        auth_service.db.refresh(test_user_profile)
        assert test_user_profile.ai_analysis == analysis

    @pytest.mark.asyncio
    async def test_store_ai_analysis_profile_not_found(self, auth_service):
        """Test storing AI analysis for non-existent profile."""
        analysis = {"test": "data"}
        
        with pytest.raises(ValueError, match="User profile not found"):
            await auth_service.store_ai_analysis("nonexistent-user-id", analysis)

    @pytest.mark.asyncio
    async def test_send_password_reset_success(self, auth_service, test_user):
        """Test sending password reset email."""
        result = await auth_service.send_password_reset(test_user.email)
        
        assert result["success"] is True
        assert "Password reset email sent" in result["message"]

    @pytest.mark.asyncio
    async def test_send_password_reset_user_not_found(self, auth_service):
        """Test sending password reset for non-existent user."""
        result = await auth_service.send_password_reset("nonexistent@example.com")
        
        assert result["success"] is False
        assert "User not found" in result["message"]