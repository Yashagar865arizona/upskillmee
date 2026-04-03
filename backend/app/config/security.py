"""
Security configuration and utilities for the Ponder application.
"""

import os
import secrets
from typing import Dict, List, Optional, Set
from datetime import timedelta
from pydantic_settings import BaseSettings
from pydantic import Field
from .settings import settings

class SecurityConfig(BaseSettings):
    """Security configuration settings"""
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Configuration
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 128
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Rate Limiting Configuration
    RATE_LIMIT_DEFAULT_REQUESTS: int = 100
    RATE_LIMIT_DEFAULT_WINDOW: int = 60  # seconds
    RATE_LIMIT_AUTH_REQUESTS: int = 10
    RATE_LIMIT_AUTH_WINDOW: int = 60
    RATE_LIMIT_CHAT_REQUESTS: int = 30
    RATE_LIMIT_CHAT_WINDOW: int = 60
    RATE_LIMIT_UPLOAD_REQUESTS: int = 5
    RATE_LIMIT_UPLOAD_WINDOW: int = 60
    
    # Input Validation Configuration
    MAX_STRING_LENGTH: int = 10000
    MAX_JSON_SIZE: int = 1024 * 1024  # 1MB
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_REQUEST_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # CORS Configuration
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_MAX_AGE: int = 86400  # 24 hours
    
    # Security Headers Configuration
    ENABLE_HSTS: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    HSTS_INCLUDE_SUBDOMAINS: bool = True
    HSTS_PRELOAD: bool = True
    
    ENABLE_CSP: bool = True
    CSP_DEFAULT_SRC: List[str] = ["'self'"]
    CSP_SCRIPT_SRC: List[str] = ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net"]
    CSP_STYLE_SRC: List[str] = ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"]
    CSP_FONT_SRC: List[str] = ["'self'", "https://fonts.gstatic.com"]
    CSP_IMG_SRC: List[str] = ["'self'", "data:", "https:"]
    CSP_CONNECT_SRC: List[str] = ["'self'", "ws:", "wss:"]
    
    # File Upload Configuration
    ALLOWED_FILE_EXTENSIONS: Set[str] = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.doc', '.docx'}
    ALLOWED_MIME_TYPES: Set[str] = {
        'image/jpeg', 'image/png', 'image/gif',
        'application/pdf', 'text/plain',
        'application/msword', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    # Content Type Validation
    ALLOWED_CONTENT_TYPES: Set[str] = {
        'application/json',
        'application/x-www-form-urlencoded',
        'multipart/form-data',
        'text/plain'
    }
    
    # Blocked User Agents (basic bot protection)
    BLOCKED_USER_AGENTS: List[str] = [
        'bot', 'crawler', 'spider', 'scraper',
        'curl', 'wget', 'python-requests'
    ]
    
    # IP Whitelist/Blacklist (empty by default)
    IP_WHITELIST: List[str] = []
    IP_BLACKLIST: List[str] = []
    
    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = True

# Create global security config instance
security_config = SecurityConfig()

def get_cors_origins() -> List[str]:
    """Get CORS origins based on environment"""
    if settings.is_production:
        return [
            "https://app.ponder.school",
            "https://ponder.school",
            "wss://app.ponder.school",
            "wss://ponder.school"
        ]
    else:
        return [
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://localhost:3002",
            "ws://localhost:3000",
            "ws://localhost:3001",
            "ws://localhost:3002",
            "ws://localhost:8000",
            "http://127.0.0.1:3000",
            "ws://127.0.0.1:3000"
        ]

def get_allowed_methods() -> List[str]:
    """Get allowed HTTP methods"""
    return ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

def get_allowed_headers() -> List[str]:
    """Get allowed request headers"""
    return [
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Request-ID",
        "Cache-Control"
    ]

def get_exposed_headers() -> List[str]:
    """Get headers to expose to client"""
    return [
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining", 
        "X-RateLimit-Reset",
        "X-Health-Status"
    ]

def get_security_headers() -> Dict[str, str]:
    """Get security headers to add to responses"""
    headers = {
        # Prevent clickjacking
        'X-Frame-Options': 'DENY',
        
        # Prevent MIME type sniffing
        'X-Content-Type-Options': 'nosniff',
        
        # Enable XSS protection
        'X-XSS-Protection': '1; mode=block',
        
        # Referrer policy
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        
        # Server identification
        'Server': 'Ponder-API',
        
        # Cache control for sensitive endpoints
        'Cache-Control': 'no-store, no-cache, must-revalidate, private',
        'Pragma': 'no-cache',
        'Expires': '0',
        
        # Permissions Policy
        'Permissions-Policy': (
            'geolocation=(), microphone=(), camera=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=()'
        )
    }
    
    # Add HSTS header for production
    if security_config.ENABLE_HSTS and settings.is_production:
        hsts_value = f'max-age={security_config.HSTS_MAX_AGE}'
        if security_config.HSTS_INCLUDE_SUBDOMAINS:
            hsts_value += '; includeSubDomains'
        if security_config.HSTS_PRELOAD:
            hsts_value += '; preload'
        headers['Strict-Transport-Security'] = hsts_value
    
    # Add CSP header
    if security_config.ENABLE_CSP:
        csp_directives = [
            f"default-src {' '.join(security_config.CSP_DEFAULT_SRC)}",
            f"script-src {' '.join(security_config.CSP_SCRIPT_SRC)}",
            f"style-src {' '.join(security_config.CSP_STYLE_SRC)}",
            f"font-src {' '.join(security_config.CSP_FONT_SRC)}",
            f"img-src {' '.join(security_config.CSP_IMG_SRC)}",
            f"connect-src {' '.join(security_config.CSP_CONNECT_SRC)}",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        headers['Content-Security-Policy'] = '; '.join(csp_directives)
    
    return headers

def get_rate_limit_config() -> Dict[str, Dict[str, int]]:
    """Get rate limiting configuration"""
    return {
        'default': {
            'requests': security_config.RATE_LIMIT_DEFAULT_REQUESTS,
            'window': security_config.RATE_LIMIT_DEFAULT_WINDOW
        },
        'auth': {
            'requests': security_config.RATE_LIMIT_AUTH_REQUESTS,
            'window': security_config.RATE_LIMIT_AUTH_WINDOW
        },
        'chat': {
            'requests': security_config.RATE_LIMIT_CHAT_REQUESTS,
            'window': security_config.RATE_LIMIT_CHAT_WINDOW
        },
        'upload': {
            'requests': security_config.RATE_LIMIT_UPLOAD_REQUESTS,
            'window': security_config.RATE_LIMIT_UPLOAD_WINDOW
        }
    }

def get_endpoint_rate_limit_mapping() -> Dict[str, str]:
    """Get mapping of endpoint patterns to rate limit categories"""
    return {
        '/api/v1/auth/': 'auth',
        '/auth/': 'auth',
        '/api/v1/chat/': 'chat',
        '/chat/': 'chat',
        '/upload': 'upload',
        '/api/v1/users/me/avatar': 'upload'
    }

def is_safe_user_agent(user_agent: str) -> bool:
    """Check if user agent is safe (not a blocked bot)"""
    if not user_agent:
        return False
    
    user_agent_lower = user_agent.lower()
    for blocked_agent in security_config.BLOCKED_USER_AGENTS:
        if blocked_agent in user_agent_lower:
            return False
    
    return True

def is_allowed_ip(ip_address: str) -> bool:
    """Check if IP address is allowed"""
    # If whitelist is configured, only allow whitelisted IPs
    if security_config.IP_WHITELIST:
        return ip_address in security_config.IP_WHITELIST
    
    # If blacklist is configured, block blacklisted IPs
    if security_config.IP_BLACKLIST:
        return ip_address not in security_config.IP_BLACKLIST
    
    # If no lists configured, allow all IPs
    return True

def validate_file_upload(filename: str, content_type: str, file_size: int) -> tuple[bool, str]:
    """Validate file upload parameters"""
    # Check file size
    if file_size > security_config.MAX_FILE_SIZE:
        return False, f"File size exceeds maximum allowed size of {security_config.MAX_FILE_SIZE} bytes"
    
    # Check file extension
    if filename:
        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext not in security_config.ALLOWED_FILE_EXTENSIONS:
            return False, f"File extension '{file_ext}' not allowed"
    
    # Check MIME type
    if content_type not in security_config.ALLOWED_MIME_TYPES:
        return False, f"Content type '{content_type}' not allowed"
    
    # Check for path traversal in filename
    if filename and ('..' in filename or '/' in filename or '\\' in filename):
        return False, "Invalid filename"
    
    return True, "File validation passed"

# Security utility functions
def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)

def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return generate_secure_token(32)

def constant_time_compare(a: str, b: str) -> bool:
    """Constant time string comparison to prevent timing attacks"""
    return secrets.compare_digest(a.encode('utf-8'), b.encode('utf-8'))