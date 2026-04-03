"""
Input validation decorators and utilities for API endpoints.
"""

import functools
import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union
from fastapi import HTTPException, Request, status
from pydantic import BaseModel, ValidationError
from ..schemas.validation import (
    validate_no_sql_injection, validate_no_xss, sanitize_html,
    validate_string_length, SecureBaseModel
)

logger = logging.getLogger(__name__)

def validate_input(
    schema: Optional[Type[BaseModel]] = None,
    sanitize: bool = True,
    max_depth: int = 10
):
    """
    Decorator to validate and sanitize input data for API endpoints.
    
    Args:
        schema: Pydantic model to validate against
        sanitize: Whether to sanitize string inputs
        max_depth: Maximum nesting depth for JSON validation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Find request object in arguments
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if request:
                    # Validate request data
                    await _validate_request_data(request, schema, sanitize, max_depth)
                
                # Call the original function
                return await func(*args, **kwargs)
                
            except ValidationError as e:
                logger.warning(f"Input validation failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Input validation failed: {str(e)}"
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Input validation error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Input validation error"
                )
        
        return wrapper
    return decorator

async def _validate_request_data(
    request: Request,
    schema: Optional[Type[BaseModel]],
    sanitize: bool,
    max_depth: int
):
    """Validate request data against schema and security patterns."""
    
    # Validate query parameters
    if request.query_params:
        for key, value in request.query_params.items():
            _validate_string_field(key, "query parameter key")
            _validate_string_field(value, f"query parameter '{key}'")
    
    # Validate headers (only custom headers)
    dangerous_headers = ['x-forwarded-host', 'x-original-url', 'x-rewrite-url']
    for header_name, header_value in request.headers.items():
        if header_name.lower().startswith('x-') and header_name.lower() not in ['x-requested-with', 'x-request-id']:
            if header_name.lower() in dangerous_headers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Dangerous header detected: {header_name}"
                )
            _validate_string_field(header_value, f"header '{header_name}'")
    
    # Validate request body if present
    if request.method in ['POST', 'PUT', 'PATCH']:
        content_type = request.headers.get('content-type', '').lower()
        
        if 'application/json' in content_type:
            try:
                body = await request.body()
                if body:
                    import json
                    json_data = json.loads(body)
                    
                    # Validate JSON structure and content
                    _validate_json_data(json_data, max_depth=max_depth)
                    
                    # Apply schema validation if provided
                    if schema and issubclass(schema, BaseModel):
                        try:
                            validated_data = schema(**json_data)
                            # Replace request body with validated data
                            sanitized_body = validated_data.json().encode()
                            request._body = sanitized_body
                        except ValidationError as e:
                            raise HTTPException(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Schema validation failed: {str(e)}"
                            )
                    
                    # Sanitize if requested
                    if sanitize:
                        sanitized_data = _sanitize_json_data(json_data)
                        sanitized_body = json.dumps(sanitized_data).encode()
                        request._body = sanitized_body
                        
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON in request body"
                )

def _validate_string_field(value: str, field_name: str):
    """Validate a string field for security issues."""
    if not isinstance(value, str):
        return
    
    try:
        # Check for SQL injection
        validate_no_sql_injection(value)
        
        # Check for XSS
        validate_no_xss(value)
        
        # Check length
        validate_string_length(value, max_length=10000)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security validation failed for {field_name}: {str(e)}"
        )

def _validate_json_data(data: Any, current_depth: int = 0, max_depth: int = 10):
    """Recursively validate JSON data structure and content."""
    
    if current_depth > max_depth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"JSON nesting too deep (max {max_depth} levels)"
        )
    
    if isinstance(data, dict):
        if len(data) > 100:  # Limit object size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON object too large (max 100 keys)"
            )
        
        for key, value in data.items():
            _validate_string_field(str(key), f"JSON key at depth {current_depth}")
            _validate_json_data(value, current_depth + 1, max_depth)
            
    elif isinstance(data, list):
        if len(data) > 1000:  # Limit array size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON array too large (max 1000 items)"
            )
        
        for i, item in enumerate(data):
            _validate_json_data(item, current_depth + 1, max_depth)
            
    elif isinstance(data, str):
        _validate_string_field(data, f"JSON string at depth {current_depth}")
        
    elif isinstance(data, (int, float)):
        # Validate numeric ranges
        if isinstance(data, int) and abs(data) > 2**53:  # JavaScript safe integer limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Integer value too large"
            )
        if isinstance(data, float) and (data != data or abs(data) == float('inf')):  # NaN or Infinity
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid numeric value"
            )

def _sanitize_json_data(data: Any) -> Any:
    """Recursively sanitize JSON data."""
    if isinstance(data, dict):
        return {key: _sanitize_json_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_sanitize_json_data(item) for item in data]
    elif isinstance(data, str):
        return sanitize_html(data)
    else:
        return data

# Specific validation decorators for common use cases

def validate_auth_input(func: Callable) -> Callable:
    """Decorator specifically for authentication endpoints."""
    from ..schemas.validation import SecureUserLogin, SecureUserRegistration
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Apply strict validation for auth endpoints
        return await validate_input(
            schema=None,  # Schema validation handled by endpoint
            sanitize=True,
            max_depth=3
        )(func)(*args, **kwargs)
    
    return wrapper

def validate_chat_input(func: Callable) -> Callable:
    """Decorator specifically for chat endpoints."""
    from ..schemas.validation import SecureChatMessage
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await validate_input(
            schema=SecureChatMessage,
            sanitize=True,
            max_depth=5
        )(func)(*args, **kwargs)
    
    return wrapper

def validate_file_upload(func: Callable) -> Callable:
    """Decorator specifically for file upload endpoints."""
    from ..schemas.validation import SecureFileUpload
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Additional file upload validation
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if request:
            await _validate_file_upload_request(request)
        
        return await validate_input(
            schema=None,  # File uploads use different validation
            sanitize=False,  # Don't sanitize binary data
            max_depth=2
        )(func)(*args, **kwargs)
    
    return wrapper

async def _validate_file_upload_request(request: Request):
    """Validate file upload request."""
    content_type = request.headers.get('content-type', '').lower()
    
    if not content_type.startswith('multipart/form-data'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File uploads must use multipart/form-data"
        )
    
    # Check content length
    content_length = request.headers.get('content-length')
    if content_length:
        try:
            size = int(content_length)
            max_size = 10 * 1024 * 1024  # 10MB
            if size > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Maximum size: {max_size} bytes"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid content-length header"
            )

# Rate limiting decorator
def rate_limit(requests_per_minute: int = 60):
    """
    Decorator to apply rate limiting to specific endpoints.
    
    Args:
        requests_per_minute: Maximum requests per minute for this endpoint
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                await _check_endpoint_rate_limit(request, requests_per_minute)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

async def _check_endpoint_rate_limit(request: Request, requests_per_minute: int):
    """Check rate limit for specific endpoint."""
    import time
    from ..config.security import security_config
    
    # Get client identifier
    client_ip = request.client.host if request.client else 'unknown'
    forwarded_for = request.headers.get('x-forwarded-for')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    
    # Create rate limit key
    endpoint = request.url.path
    current_minute = int(time.time() // 60)
    rate_limit_key = f"endpoint_rate_limit:{endpoint}:{client_ip}:{current_minute}"
    
    # Simple in-memory rate limiting (in production, use Redis)
    if not hasattr(_check_endpoint_rate_limit, 'memory_store'):
        _check_endpoint_rate_limit.memory_store = {}
    
    current_requests = _check_endpoint_rate_limit.memory_store.get(rate_limit_key, 0)
    
    if current_requests >= requests_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {requests_per_minute} requests per minute.",
            headers={"Retry-After": "60"}
        )
    
    # Increment counter
    _check_endpoint_rate_limit.memory_store[rate_limit_key] = current_requests + 1
    
    # Clean up old entries (keep only current minute)
    keys_to_remove = [
        key for key in _check_endpoint_rate_limit.memory_store.keys()
        if not key.endswith(str(current_minute))
    ]
    for key in keys_to_remove:
        del _check_endpoint_rate_limit.memory_store[key]