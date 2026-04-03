"""
Enhanced input validation schemas with comprehensive security checks.
"""

import re
import html
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Common validation patterns
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$")
URL_PATTERN = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# Security validation patterns
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
    r"(--|#|/\*|\*/)",
    r"(\bOR\b.*=.*\bOR\b)",
    r"(\bAND\b.*=.*\bAND\b)",
    r"(1=1|1=0)",
]

XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>.*?</iframe>",
]

def validate_no_sql_injection(value: str) -> str:
    """Validate that input doesn't contain SQL injection patterns"""
    if not isinstance(value, str):
        return value
    
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValueError("Input contains potentially malicious SQL patterns")
    
    return value

def validate_no_xss(value: str) -> str:
    """Validate that input doesn't contain XSS patterns"""
    if not isinstance(value, str):
        return value
    
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValueError("Input contains potentially malicious script patterns")
    
    return value

def sanitize_html(value: str) -> str:
    """Sanitize HTML content"""
    if not isinstance(value, str):
        return value
    
    # HTML escape the content
    sanitized = html.escape(value)
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    return sanitized

def validate_string_length(value: str, min_length: int = 0, max_length: int = 1000) -> str:
    """Validate string length"""
    if not isinstance(value, str):
        return value
    
    if len(value) < min_length:
        raise ValueError(f"String too short. Minimum length: {min_length}")
    
    if len(value) > max_length:
        raise ValueError(f"String too long. Maximum length: {max_length}")
    
    return value

class SecureBaseModel(BaseModel):
    """Base model with security validations"""
    
    model_config = ConfigDict(
        # Validate assignment to prevent bypassing validation
        validate_assignment=True,
        # Use enum values instead of names
        use_enum_values=True,
        # Allow population by field name
        populate_by_name=True
    )

class SecureStringField(str):
    """Custom string field with security validation"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, value):
        if not isinstance(value, str):
            raise TypeError('string required')
        
        # Apply security validations
        value = validate_no_sql_injection(value)
        value = validate_no_xss(value)
        value = sanitize_html(value)
        
        return cls(value)

class EmailField(str):
    """Validated email field"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, value):
        if not isinstance(value, str):
            raise TypeError('string required')
        
        # Basic security checks
        value = validate_no_sql_injection(value)
        value = validate_no_xss(value)
        
        # Email format validation
        if not EMAIL_PATTERN.match(value):
            raise ValueError('Invalid email format')
        
        # Length validation
        if len(value) > 254:  # RFC 5321 limit
            raise ValueError('Email address too long')
        
        return cls(value.lower())

class PasswordField(str):
    """Validated password field"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, value):
        if not isinstance(value, str):
            raise TypeError('string required')
        
        # Length validation
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if len(value) > 128:
            raise ValueError('Password too long')
        
        # Complexity validation
        if not PASSWORD_PATTERN.match(value):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one digit, and one special character'
            )
        
        return cls(value)

class UsernameField(str):
    """Validated username field"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, value):
        if not isinstance(value, str):
            raise TypeError('string required')
        
        # Basic security checks
        value = validate_no_sql_injection(value)
        value = validate_no_xss(value)
        
        # Username format validation
        if not USERNAME_PATTERN.match(value):
            raise ValueError(
                'Username must be 3-30 characters long and contain only '
                'letters, numbers, underscores, and hyphens'
            )
        
        return cls(value.lower())

class URLField(str):
    """Validated URL field"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, value):
        if not isinstance(value, str):
            raise TypeError('string required')
        
        # Basic security checks
        value = validate_no_sql_injection(value)
        value = validate_no_xss(value)
        
        # URL format validation
        if not URL_PATTERN.match(value):
            raise ValueError('Invalid URL format')
        
        # Length validation
        if len(value) > 2048:
            raise ValueError('URL too long')
        
        return cls(value)

class UUIDField(str):
    """Validated UUID field"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, value):
        if not isinstance(value, str):
            raise TypeError('string required')
        
        # UUID format validation
        if not UUID_PATTERN.match(value.lower()):
            raise ValueError('Invalid UUID format')
        
        return cls(value.lower())

# Enhanced validation schemas for common use cases

class SecureUserRegistration(SecureBaseModel):
    """Secure user registration schema"""
    username: UsernameField
    email: EmailField
    password: PasswordField
    full_name: Optional[SecureStringField] = Field(None, max_length=100)
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        if v is not None:
            v = validate_string_length(v, 1, 100)
        return v

class SecureUserLogin(SecureBaseModel):
    """Secure user login schema"""
    email: EmailField
    password: str = Field(..., min_length=1, max_length=128)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        # Don't validate password complexity on login (only on registration)
        # Just check for basic security issues
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        return v

class SecureChatMessage(SecureBaseModel):
    """Secure chat message schema"""
    message: SecureStringField = Field(..., min_length=1, max_length=4000)
    user_id: Optional[UUIDField] = None
    conversation_id: Optional[UUIDField] = None
    agent_mode: Optional[str] = Field(None, pattern=r"^(chat|work|plan)$")
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @field_validator('message')
    @classmethod
    def validate_message_content(cls, v):
        # Additional validation for chat messages
        v = validate_string_length(v, 1, 4000)
        
        # Check for excessive repetition (potential spam)
        if len(set(v.lower().split())) < len(v.split()) * 0.3:
            logger.warning("Message with excessive repetition detected")
        
        return v
    
    @field_validator('context', 'metadata')
    @classmethod
    def validate_json_fields(cls, v):
        if v is not None:
            # Validate that JSON fields don't contain malicious content
            json_str = str(v)
            validate_no_sql_injection(json_str)
            validate_no_xss(json_str)
        return v

class SecureUserProfile(SecureBaseModel):
    """Secure user profile schema"""
    name: Optional[SecureStringField] = Field(None, max_length=100)
    email: Optional[EmailField] = None
    bio: Optional[SecureStringField] = Field(None, max_length=500)
    location: Optional[SecureStringField] = Field(None, max_length=100)
    learning_level: Optional[str] = Field(None, pattern=r"^(beginner|intermediate|advanced|expert)$")
    preferred_subjects: Optional[List[SecureStringField]] = None
    career_interests: Optional[List[SecureStringField]] = None
    technical_skills: Optional[List[SecureStringField]] = None
    soft_skills: Optional[List[SecureStringField]] = None
    long_term_goals: Optional[List[SecureStringField]] = None
    achievements: Optional[List[SecureStringField]] = None
    preferences: Optional[Dict[str, Any]] = None
    
    @field_validator('preferred_subjects', 'career_interests', 'technical_skills', 
              'soft_skills', 'long_term_goals', 'achievements')
    @classmethod
    def validate_string_lists(cls, v):
        if v is not None:
            if len(v) > 20:  # Limit array size
                raise ValueError("Too many items in list")
            
            for item in v:
                if len(item) > 100:  # Limit individual item length
                    raise ValueError("List item too long")
        return v
    
    @field_validator('preferences')
    @classmethod
    def validate_preferences(cls, v):
        if v is not None:
            # Validate preferences JSON
            json_str = str(v)
            validate_no_sql_injection(json_str)
            validate_no_xss(json_str)
            
            # Limit preferences size
            if len(json_str) > 5000:
                raise ValueError("Preferences data too large")
        return v

class SecureFileUpload(SecureBaseModel):
    """Secure file upload schema"""
    filename: SecureStringField = Field(..., max_length=255)
    content_type: str = Field(..., max_length=100)
    size: int = Field(..., gt=0, le=10*1024*1024)  # Max 10MB
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        # Check for path traversal in filename
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("Invalid filename")
        
        # Check file extension
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.doc', '.docx'}
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError("File type not allowed")
        
        return v
    
    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v):
        allowed_types = {
            'image/jpeg', 'image/png', 'image/gif',
            'application/pdf', 'text/plain',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        if v not in allowed_types:
            raise ValueError("Content type not allowed")
        
        return v

class SecurePasswordReset(SecureBaseModel):
    """Secure password reset schema"""
    email: EmailField
    
class SecurePasswordResetConfirm(SecureBaseModel):
    """Secure password reset confirmation schema"""
    token: SecureStringField = Field(..., min_length=32, max_length=64)
    new_password: PasswordField
    
    @field_validator('token')
    @classmethod
    def validate_token(cls, v):
        # Token should only contain alphanumeric characters and basic symbols
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Invalid token format")
        return v

class SecureTokenRefresh(SecureBaseModel):
    """Secure token refresh schema"""
    refresh_token: SecureStringField = Field(..., min_length=10, max_length=1000)

# Rate limiting schemas
class RateLimitInfo(SecureBaseModel):
    """Rate limit information"""
    limit: int
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None

# Error response schemas
class SecurityError(SecureBaseModel):
    """Security error response"""
    error: str
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))