"""
Router for authentication operations.
Key features:
- User registration and login
- Email verification
- Password reset
- Token management
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import re

from ..database import get_db
from ..services.auth_service import AuthService
from ..models.user import User
from ..schemas.validation import (
    SecureUserRegistration, SecureUserLogin, SecurePasswordReset,
    SecurePasswordResetConfirm, SecureTokenRefresh, EmailField,
    SecureStringField, PasswordField, UsernameField
)

logger = logging.getLogger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Enhanced schema models with security validation
class UserCreate(SecureUserRegistration):
    """Enhanced schema for user registration with security validation"""
    pass

class LoginRequest(SecureUserLogin):
    """Enhanced schema for login request with security validation"""
    pass

class RegisterOrLoginRequest(BaseModel):
    """Schema for combined register/login request"""
    email: EmailField
    password: SecureStringField = Field(..., min_length=1, max_length=128)
    full_name: Optional[SecureStringField] = Field(None, max_length=100)
    is_new_user: Optional[bool] = False

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user_id: str

class EmailVerificationRequest(BaseModel):
    """Schema for email verification"""
    token: SecureStringField = Field(..., min_length=32, max_length=64)
    
    @validator('token')
    def validate_token_format(cls, v):
        # Token should only contain safe characters
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Invalid token format")
        return v$', v):
            raise ValueError("Invalid token format")
        return v$', v):
            raise ValueError("Invalid token format")
        return v$', v):
            raise ValueError("Invalid token format")
        return v$', v):
            raise ValueError("Invalid token format")
        return v$', v):
            raise ValueError("Invalid token format")
        return v$', v):
            raise ValueError("Invalid token format")
        return v$', v):
            raise ValueError("Invalid token format")
        return v$', v):
            raise ValueError("Invalid token format")
        return v$', v):
            raise ValueError("Invalid token format")
        return v$', v):
            raise ValueError("Invalid token format")
        return v$', v):
            raise ValueError("Invalid token format")
        return v

class PasswordResetRequest(SecurePasswordReset):
    """Enhanced schema for password reset request with security validation"""
    pass

class PasswordResetConfirmation(SecurePasswordResetConfirm):
    """Enhanced schema for password reset confirmation with security validation"""
    pass

class RefreshTokenRequest(SecureTokenRefresh):
    """Enhanced schema for refresh token request with security validation"""
    pass

# Get service instances
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get instance of AuthService with proper configuration"""
    return AuthService(db)

# Create a class-based router for backward compatibility
class AuthRouter:
    def __init__(self):
        self.router = APIRouter()
        self._setup_routes()
        
    def _setup_routes(self):
        # Register all routes on the router
        self.router.add_api_route("/register", self.register_user, methods=["POST"], response_model=Dict[str, Any])
        self.router.add_api_route("/login", self.login, methods=["POST"], response_model=TokenResponse)
        self.router.add_api_route("/register-or-login", self.register_or_login, methods=["POST"], response_model=TokenResponse)
        self.router.add_api_route("/logout", self.logout, methods=["POST"])
        self.router.add_api_route("/verify-email", self.verify_email, methods=["POST"])
        self.router.add_api_route("/reset-password", self.request_password_reset, methods=["POST"])
        self.router.add_api_route("/reset-password-confirm", self.confirm_password_reset, methods=["POST"])
        self.router.add_api_route("/refresh", self.refresh_token, methods=["POST"], response_model=TokenResponse)
        self.router.add_api_route("/me", self.get_current_user, methods=["GET"])
        
    async def register_user(
        self,
        user: UserCreate,
        background_tasks: BackgroundTasks,
        auth_service: AuthService = Depends(get_auth_service)
    ) -> Dict[str, Any]:
        """Register a new user."""
        try:
            result = await auth_service.register_user(
                username=user.username,
                email=user.email,
                password=user.password,
                full_name=user.full_name,
                background_tasks=background_tasks
            )
            
            return {
                "status": "success",
                "message": "User registered successfully. Please check your email for verification.",
                "user_id": result["user_id"]
            }
        except ValueError as e:
            logger.error(f"Registration error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during registration"
            )

    async def register_or_login(
        self,
        data: RegisterOrLoginRequest,
        background_tasks: BackgroundTasks,
        auth_service: AuthService = Depends(get_auth_service)
    ) -> TokenResponse:
        """Register a new user or login existing user based on request."""
        try:
            # Check if this is intended as a registration
            if data.is_new_user:
                # Try to register the user
                try:
                    result = await auth_service.register_user(
                        username=data.email.split('@')[0],  # Use email prefix as username
                        email=data.email,
                        password=data.password,
                        full_name=data.full_name,
                        background_tasks=background_tasks
                    )
                    
                    # Auto-login after registration
                    auth_result = await auth_service.authenticate_user(
                        email=data.email,
                        password=data.password
                    )
                    
                    if not auth_result["success"]:
                        # This should not happen if registration was successful
                        logger.warning(f"Failed to auto-login after registration: {data.email}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Registration successful but login failed"
                        )
                        
                    return TokenResponse(
                        access_token=auth_result["access_token"],
                        token_type="bearer",
                        expires_in=auth_result["expires_in"],
                        refresh_token=auth_result.get("refresh_token"),
                        user_id=auth_result["user_id"]
                    )
                    
                except ValueError as e:
                    # If user already exists, try to log them in instead
                    if "already exists" in str(e).lower():
                        logger.info(f"User already exists, attempting login instead: {data.email}")
                    else:
                        # For other registration errors, raise the exception
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e)
                        )
            
            # Login flow (either direct login or fallback from registration)
            auth_result = await auth_service.authenticate_user(
                email=data.email,
                password=data.password
            )
            
            if not auth_result["success"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            return TokenResponse(
                access_token=auth_result["access_token"],
                token_type="bearer",
                expires_in=auth_result["expires_in"],
                refresh_token=auth_result.get("refresh_token"),
                user_id=auth_result["user_id"]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Register/login error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during authentication"
            )
    
    async def login(
        self,
        login_data: LoginRequest,
        auth_service: AuthService = Depends(get_auth_service)
    ) -> TokenResponse:
        """Authenticate a user and return a token."""
        try:
            auth_result = await auth_service.authenticate_user(
                email=login_data.email,
                password=login_data.password
            )
            
            if not auth_result["success"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            return TokenResponse(
                access_token=auth_result["access_token"],
                token_type="bearer",
                expires_in=auth_result["expires_in"],
                refresh_token=auth_result.get("refresh_token"),
                user_id=auth_result["user_id"]
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during login"
            )
    
    async def logout(
        self,
        token: str = Depends(oauth2_scheme),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> Dict[str, Any]:
        """Log out a user by invalidating their token."""
        try:
            if token:
                # Invalidate the token
                success = await auth_service.invalidate_token(token)
                if success:
                    return {"status": "success", "message": "Logged out successfully"}
                else:
                    return {"status": "warning", "message": "Token may already be invalid"}
            
            return {"status": "success", "message": "Logged out successfully"}
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during logout"
            )
    
    async def verify_email(
        self,
        verification_data: EmailVerificationRequest,
        auth_service: AuthService = Depends(get_auth_service)
    ) -> Dict[str, Any]:
        """Verify a user's email address."""
        try:
            # Verify the email
            result = await auth_service.verify_email(verification_data.token)
            
            if not result["success"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["message"]
                )
            
            return {
                "status": "success",
                "message": "Email verified successfully",
                "user_id": result["user_id"]
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during email verification"
            )
    
    async def request_password_reset(
        self,
        reset_data: PasswordResetRequest,
        background_tasks: BackgroundTasks,
        auth_service: AuthService = Depends(get_auth_service)
    ) -> Dict[str, Any]:
        """Request a password reset."""
        try:
            # Send password reset email
            await auth_service.send_password_reset(
                email=reset_data.email,
                background_tasks=background_tasks
            )
            
            return {
                "status": "success",
                "message": "If the email exists, a password reset link has been sent"
            }
        except Exception as e:
            logger.error(f"Password reset request error: {str(e)}")
            # Don't expose whether the email exists or not
            return {
                "status": "success",
                "message": "If the email exists, a password reset link has been sent"
            }
    
    async def confirm_password_reset(
        self,
        confirmation_data: PasswordResetConfirmation,
        auth_service: AuthService = Depends(get_auth_service)
    ) -> Dict[str, Any]:
        """Confirm a password reset."""
        try:
            # Reset the password
            result = await auth_service.reset_password(
                token=confirmation_data.token,
                new_password=confirmation_data.new_password
            )
            
            if not result["success"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["message"]
                )
            
            return {
                "status": "success",
                "message": "Password reset successfully"
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password reset confirmation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during password reset"
            )
    
    async def refresh_token(
        self,
        refresh_data: RefreshTokenRequest,
        auth_service: AuthService = Depends(get_auth_service)
    ) -> TokenResponse:
        """Refresh access token using refresh token."""
        try:
            result = await auth_service.refresh_access_token(refresh_data.refresh_token)
            
            if not result["success"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=result["message"],
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            return TokenResponse(
                access_token=result["access_token"],
                token_type="bearer",
                expires_in=result["expires_in"],
                user_id=result["user_id"]
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during token refresh"
            )
    
    def get_current_user_dependency(
        self,
        token: str = Depends(oauth2_scheme),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> User:
        """Dependency to get the current authenticated user from the bearer token."""
        try:
            # Get user from token
            user = auth_service.get_current_user(token)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            return user
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication error",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> Dict[str, Any]:
        """Get the current authenticated user's data."""
        logger.debug(f"get_current_user called with token: {token[:10] if token and len(token) > 10 else token}...")
        
        try:
            # Get user from token
            user = auth_service.get_current_user(token)
            logger.debug(f"User lookup result: {user is not None}")
            
            if not user:
                logger.warning("Invalid token - no user found")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token - no user found",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Return user data
            user_data = {
                "id": str(user.id),
                "username": user.name,
                "email": user.email,
                "full_name": user.name,
                "is_active": user.is_active,
                "is_verified": user.is_verified
            }
            logger.debug(f"Returning user data for user ID: {user.id}")
            return user_data
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication error: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )

# Create and export the router object with backward compatibility structure
router = AuthRouter()
