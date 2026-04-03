"""
Router for authentication operations with enhanced security.
Key features:
- User registration and login with input validation
- Email verification
- Password reset
- Token management
- Rate limiting and security hardening
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header, Request,Form, File, UploadFile
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import re
from app.utils.security import get_password_hash
from ..database import get_db
from ..services.auth_service import AuthService
from ..models.user import User,PendingUserEmail,Psychometric
from pydantic import EmailStr
from app.schemas.otp import SendOtpRequest,VerifyOtpRequest
from app.services.otp_service import send_otp,verify_otp
from app.services.oauth_service import oauth, get_user_info
from fastapi.responses import HTMLResponse
import json
from fastapi.responses import RedirectResponse
from fastapi.encoders import jsonable_encoder
from app.routers.user_router import get_current_user_dependency
from app.schemas.auth import UserUpdateRequest
import os
from uuid import uuid4
from app.services.email_service import send_verification_email
from app.config.settings import settings
from fastapi.responses import RedirectResponse
import jwt

logger = logging.getLogger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Simple schema models for auth
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(None, min_length=7, max_length=15)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Email or phone number")
    password: str

class EmailSubmitSchema(BaseModel):
    email: EmailStr
    
class SubmitSchema(BaseModel):
    email: EmailStr
    name: str
    phone_number: str = None
    message: str = None

class RegisterOrLoginRequest(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: str
    is_new_user: Optional[bool] = False  
    is_email_verified: Optional[bool] = False    
    is_phone_verified: Optional[bool] = False 


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user_id: str

class EmailVerificationRequest(BaseModel):
    """Schema for email verification"""
    token: str = Field(..., min_length=10, max_length=100)

class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: str = Field(..., min_length=5, max_length=100)

class PasswordResetConfirmation(BaseModel):
    """Schema for password reset confirmation"""
    token: str = Field(..., min_length=10, max_length=100)
    new_password: str = Field(..., min_length=6, max_length=128)

class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str = Field(..., min_length=10, max_length=1000)

class ResetPasswordWithOtpRequest(BaseModel):
    email: Optional[str] = None
    phone_number: Optional[str] = None
    otp: str = Field(..., min_length=4, max_length=6)
    new_password: str = Field(..., min_length=6, max_length=128)

    def validate_input(self):
        if not self.email and not self.phone_number:
            raise ValueError("Either email or phone number must be provided")
        if self.email and self.phone_number:
            raise ValueError("Provide only one of email or phone number")

# Get service instances
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get instance of AuthService with proper configuration"""
    return AuthService(db)

# Create router
router = APIRouter()

@router.post("/register", response_model=Dict[str, Any])
async def register_user(
    user: UserCreate,  # <-- schema updated to include username & phone_number
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Register a new user."""
    pending = db.query(PendingUserEmail).filter_by(email=user.email, is_verified_by_admin=True).first()
    if not pending:
        raise HTTPException(status_code=403, detail="Email not verified by admin")
    try:
        result = auth_service.register_user(
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            password=user.password,
            phone_number=user.phone_number, 
            background_tasks=background_tasks
        )
        db.delete(pending)
        db.commit()
        return {
            "status": "success",
            "message": "User registered successfully. Please check your email for verification.",
            "user_id": result["user_id"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not register user")

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    auth_result = auth_service.authenticate_user(
        identifier=login_data.identifier,
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


@router.post("/register-or-login", response_model=TokenResponse)
async def register_or_login(
    data: RegisterOrLoginRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Combined endpoint for:
    1️  First-time users: register after admin email approval.
    2️ Existing users: login with email or phone.
    """

    identifier = data.email or data.phone_number

    # Check if email is verified by admin before allowing registration
    if data.is_new_user:
        if not data.email:
            raise HTTPException(status_code=400, detail="Email is required for new user registration")

        pending = db.query(PendingUserEmail).filter_by(email=data.email, is_verified_by_admin=True).first()
        if not pending:
            raise HTTPException(status_code=403, detail="Your email is not yet approved by admin")

        # Use email as username if not provided
        username = data.username or data.email.split("@")[0]

        try:
            # Register user
            result = auth_service.register_user(
                username=username,
                full_name=data.full_name,
                email=data.email,
                phone_number=data.phone_number,
                password=data.password,
                is_email_verified=data.is_email_verified,
                is_phone_verified=data.is_phone_verified,
                background_tasks=background_tasks
            )

            # Remove from pending table
            db.delete(pending)
            db.commit()

        except ValueError as e:
            if "already exists" in str(e).lower():
                # Fallback to login
                pass
            else:
                raise HTTPException(status_code=400, detail=str(e))

    # Authenticate user (email or phone)
    auth_result = auth_service.authenticate_user(
        identifier=identifier,
        password=data.password
    )

    if not auth_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or email not approved",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Return token and user info
    return TokenResponse(
        access_token=auth_result["access_token"],
        token_type="bearer",
        expires_in=auth_result["expires_in"],
        refresh_token=auth_result.get("refresh_token"),
        user_id=auth_result["user_id"]
    )


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """Log out a user by invalidating their token."""
    try:
        if token:
            # Invalidate the token
            success = auth_service.invalidate_token(token)
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

@router.post("/verify-otp")
def verify_otp_route(data: VerifyOtpRequest):
    try:
        data.validate_input()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    identifier = data.email or data.phone_number

    if not verify_otp(identifier, data.otp): 
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    return {
        "message": f"OTP verified successfully for {identifier}"
    }


@router.post("/reset-password")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """Request a password reset."""
    try:
        # Send password reset email
        auth_service.send_password_reset(
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

@router.post("/reset-password-confirm")
async def confirm_password_reset(
    confirmation_data: PasswordResetConfirmation,
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """Confirm a password reset."""
    try:
        # Reset the password
        result = auth_service.reset_password(
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

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Refresh access token using refresh token."""
    try:
        result = auth_service.refresh_access_token(refresh_data.refresh_token)
        
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

@router.get("/me")
async def get_current_user(
    request: Request,  
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get the current authenticated user's data."""
    user = auth_service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token - no user found",
            headers={"WWW-Authenticate": "Bearer"}
        )
       
    psychometric = db.query(Psychometric).filter(Psychometric.user_id == str(user.id)).first()
    test_status = psychometric.status if psychometric else "not_started"
    photo_url = None
    if user.photo_url:
        if user.photo_url.startswith("http"):
            photo_url = user.photo_url
        else:
            photo_url = f"{request.base_url}{user.photo_url.lstrip('/')}"

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.name,
        "phone_number": user.phone_number,
        "country": user.country,
        "city": user.city,
        "photo_url": photo_url,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_onboarding": user.is_onboarding,
        "psychometric_status": test_status
    }


@router.post("/send-otp")
def send_otp_route(data: SendOtpRequest):
    try:
        data.validate_input()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    identifier = data.email or data.phone_number

    success, otp = send_otp(identifier)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    
    return {
        "message": "OTP sent successfully",
        "otp": otp
    }

@router.post("/verify-otp")
def verify_otp_route(data: VerifyOtpRequest, db: Session = Depends(get_db)):
    try:
        data.validate_input()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    identifier = data.email or data.phone_number

    if not verify_otp(identifier, data.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # Find user in current or pending fields
    user = db.query(User).filter(
        (User.email == identifier) |
        (User.pending_email == identifier) |
        (User.phone_number == identifier) |
        (User.pending_phone_number == identifier)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Mark verified fields
    if user.email == identifier or user.pending_email == identifier:
        user.email = user.pending_email or user.email
        user.pending_email = None
        user.is_email_verified = True

    if user.phone_number == identifier or user.pending_phone_number == identifier:
        user.phone_number = user.pending_phone_number or user.phone_number
        user.pending_phone_number = None
        user.is_phone_verified = True

    # Activate user if at least one identifier verified
    user.is_verified = user.is_email_verified or user.is_phone_verified
    user.is_active = user.is_verified

    db.commit()
    db.refresh(user)

    return {
        "status": "success",
        "message": "OTP verified successfully.",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "phone_number": user.phone_number,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "is_email_verified": user.is_email_verified,
            "is_phone_verified": user.is_phone_verified,
        },
    }


@router.post("/reset-password-with-otp")
def reset_password_with_otp(data: ResetPasswordWithOtpRequest, db: Session = Depends(get_db)):
    try:
        data.validate_input()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    identifier = data.email or data.phone_number

    # Verify OTP
    if not verify_otp(identifier, data.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # Find user
    user = None
    if data.email:
        user = db.query(User).filter(User.email == data.email).first()
    elif data.phone_number:
        user = db.query(User).filter(User.phone_number == data.phone_number).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = get_password_hash(data.new_password)
    db.commit()

    return {"message": "Password reset successfully"}









@router.get("/oauth/google")
async def oauth_login(request: Request):
    oauth_client = oauth.create_client("google")
    redirect_uri = request.url_for("google_callback") 
    print("Using redirect_uri:", redirect_uri)
    return await oauth_client.authorize_redirect(request, redirect_uri)


@router.get("/oauth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    oauth_client = oauth.create_client("google")
    token = await oauth_client.authorize_access_token(request)

    # Fetch user info
    try:
        user_info = await oauth_client.parse_id_token(request, token)
    except Exception:
        resp = await oauth_client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo", token=token
        )
        user_info = resp.json()

    # Check if user exists
    user = db.query(User).filter(User.email == user_info["email"]).first()
    if not user:
        user = User(
            email=user_info["email"],
            name=user_info.get("name"),
            username=user_info["email"].split("@")[0],
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # ✅ Pass db to AuthService
    auth_service = AuthService(db)
    access_token = auth_service.create_access_token(user=user)

    frontend_url = f"http://localhost:3000/auth/success?token={access_token}"
    return RedirectResponse(url=frontend_url)




@router.put("/me/update", response_model=Dict[str, Any])
async def update_user_profile(
    request: Request,
    username: Optional[str] = Form(None),
    full_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Update current user's profile"""
    user = auth_service.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")

    if file:
        upload_dir = "uploads/profile_images/"
        os.makedirs(upload_dir, exist_ok=True)

        filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", file.filename)
        file_path = os.path.join(upload_dir, f"{user.id}_{filename}")

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        user.photo_url = f"/{file_path.replace(os.sep, '/')}"

    try:
        updated_user = await auth_service.update_profile(
            user=user,
            username=username,
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            country=country,
            city=city,
            request=request
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not update profile: {str(e)}")

    photo_url = None
    if updated_user.photo_url:
        if updated_user.photo_url.startswith("http"):
            photo_url = updated_user.photo_url
        else:
            photo_url = f"{request.base_url}{updated_user.photo_url.lstrip('/')}"

    return {
        "status": "success",
        "message": "Profile updated successfully",
        "user": {
            "id": str(updated_user.id),
            "username": updated_user.username,
            "full_name": updated_user.name,
            "email": updated_user.email,
            "phone_number": updated_user.phone_number,
            "country": updated_user.country,
            "city": updated_user.city,
            "photo_url": photo_url,
            "is_active": updated_user.is_active,
            "is_verified": updated_user.is_verified,
        }
    }

@router.get("/profile-completion", response_model=Dict[str, Any])
async def profile_completion(
    user: User = Depends(get_current_user_dependency),
) -> Dict[str, Any]:

    profile_fields = {
        "username": bool(user.username),
        "full_name": bool(user.name),
        "email": bool(user.email),
        "phone_number": bool(user.phone_number),
        "country": bool(user.country),
        "city": bool(user.city),
        "photo_url": bool(user.photo_url),
        "is_email_verified": user.is_email_verified,
        "is_phone_verified": user.is_phone_verified,
        "psychometric_test_completed": bool(user.psychometric_test and user.psychometric_test.status == "submitted")
    }

    total_fields = len(profile_fields)
    completed_fields = sum(value is True for value in profile_fields.values())
    completion_percentage = int((completed_fields / total_fields) * 100)

    return {
        "completion_percentage": completion_percentage,
        "completed_fields": [key for key, value in profile_fields.items() if value],
        "missing_fields": [key for key, value in profile_fields.items() if not value]
    }





@router.post("/submit-email", response_model=Dict[str, str])
def submit_email(payload: SubmitSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    existing = db.query(PendingUserEmail).filter_by(email=email).first()
    
    if existing:
        if existing.is_verified_by_admin:
            if not existing.email_sent:
                background_tasks.add_task(send_verification_email, email, settings.WEBSITE_URL)
                existing.email_sent = True
                db.commit()
            return {"message": "Your email is already approved! Check your inbox to login."}
        
        return {"message": "You have already submitted this email. Please wait for admin approval."}
    
    
    new_email = PendingUserEmail(
        email=email,
        name=payload.name.strip(),
        phone_number=payload.phone_number,
        message=payload.message
    )
    db.add(new_email)
    db.commit()
    
    return {"message": "Email submitted. Admin will verify and give access."}


@router.post("/admin/approve-email", response_model=Dict[str, str])
async def approve_email(payload: EmailSubmitSchema, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    existing = db.query(PendingUserEmail).filter_by(email=email).first()
    if not existing:
        return {"message": "Email not found."}

    if existing.is_verified_by_admin:
        return {"message": "Email already approved."}

    existing.is_verified_by_admin = True
    db.commit()

    if not existing.email_sent:
        await send_verification_email(existing.email, settings.WEBSITE_URL)
        existing.email_sent = True
        db.commit()

    return {"message": "Email approved and notification sent."}

# Dependency to get the current authenticated user from the bearer token
def get_current_user_dependency(
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