"""
Enhanced security middleware for comprehensive input validation, sanitization, and security headers.
"""

import re
import html
import json
import logging
import time
import hashlib
from typing import Dict, Any, Optional, List, Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from ..config.security import security_config, get_security_headers

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware for input validation and security headers"""
    
    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        
        # Security patterns for input validation
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b.*\b(FROM|INTO|WHERE|VALUES)\b)",
            r"(--\s*[^\r\n]*)",  # SQL comments with content
            r"(/\*.*?\*/)",  # SQL block comments
            r"(\bOR\b\s*\d+\s*=\s*\d+)",  # OR 1=1 style
            r"(\bAND\b\s*\d+\s*=\s*\d+)",  # AND 1=1 style
            r"(\bUNION\b\s+\b(ALL\s+)?\bSELECT\b)",  # UNION SELECT
            r"(\bxp_cmdshell\b)",
            r"(\bsp_executesql\b)",
            r"(\bINTO\s+OUTFILE\b)",
            r"(\bLOAD_FILE\b)",
            r"(\bCHAR\s*\(\s*\d+)",  # CHAR(number) - more specific
            r"(\bCONCAT\s*\([^)]*\bSELECT\b)",  # CONCAT with SELECT
            r"(\bSUBSTRING\s*\([^)]*\bSELECT\b)"  # SUBSTRING with SELECT
        ]
        
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
            r"<embed[^>]*>.*?</embed>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"<style[^>]*>.*?</style>",
            r"expression\s*\(",
            r"url\s*\(",
            r"@import",
            r"vbscript:",
            r"data:text/html",
            r"<svg[^>]*>.*?</svg>",
            r"<math[^>]*>.*?</math>"
        ]
        
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
            r"..%2f",
            r"..%5c",
            r"\.\.%2f",
            r"\.\.%5c",
            r"%252e%252e%252f",
            r"%c0%ae%c0%ae%c0%af"
        ]
        
        # Command injection patterns
        self.command_injection_patterns = [
            r"[;&|`$(){}[\]<>]",
            r"\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig|ping|curl|wget|nc|ncat|telnet|ssh|ftp|tftp)\b",
            r"(\|\s*\w+)",
            r"(&&\s*\w+)",
            r"(;\s*\w+)",
            r"(`[^`]*`)",
            r"(\$\([^)]*\))"
        ]
        
        # Compile patterns for better performance
        self.compiled_sql_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_injection_patterns]
        self.compiled_xss_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.xss_patterns]
        self.compiled_path_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.path_traversal_patterns]
        self.compiled_command_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.command_injection_patterns]
        
        # Use security config values
        self.allowed_content_types = security_config.ALLOWED_CONTENT_TYPES
        self.allowed_file_extensions = security_config.ALLOWED_FILE_EXTENSIONS
        self.max_file_size = security_config.MAX_FILE_SIZE
        self.max_request_size = security_config.MAX_REQUEST_SIZE
        self.max_string_length = security_config.MAX_STRING_LENGTH
        
        # Blocked user agents and IPs from config
        self.blocked_user_agents = security_config.BLOCKED_USER_AGENTS
        self.ip_whitelist = security_config.IP_WHITELIST
        self.ip_blacklist = security_config.IP_BLACKLIST
        
    async def dispatch(self, request: Request, call_next):
        """Main security middleware dispatch"""
        try:
            # Skip security checks for health endpoints
            if request.url.path in ['/', '/health', '/health/', '/metrics', '/docs', '/openapi.json']:
                response = await call_next(request)
                return self._add_security_headers(response)
            
            # Handle CORS preflight requests with minimal validation
            if request.method == "OPTIONS":
                # For OPTIONS requests, only do basic validation
                client_ip = self._get_client_ip(request)
                if not self._is_allowed_ip(client_ip):
                    logger.warning(f"Blocked IP address: {client_ip}")
                    return JSONResponse(
                        status_code=403,
                        content={"error": "Access denied"}
                    )
                
                # Process OPTIONS request with minimal security checks
                response = await call_next(request)
                return self._add_security_headers(response)
            
            # Check IP whitelist/blacklist
            client_ip = self._get_client_ip(request)
            if not self._is_allowed_ip(client_ip):
                logger.warning(f"Blocked IP address: {client_ip}")
                return JSONResponse(
                    status_code=403,
                    content={"error": "Access denied"}
                )
            
            # Check user agent
            user_agent = request.headers.get('user-agent', '')
            if not self._is_safe_user_agent(user_agent):
                logger.warning(f"Blocked user agent: {user_agent}")
                return JSONResponse(
                    status_code=403,
                    content={"error": "Access denied"}
                )
            
            # Validate request method
            if not self._validate_http_method(request):
                return JSONResponse(
                    status_code=405,
                    content={"error": "Method not allowed"}
                )
            
            # Validate content type for POST/PUT requests
            if request.method in ['POST', 'PUT', 'PATCH']:
                if not self._validate_content_type(request):
                    return JSONResponse(
                        status_code=415,
                        content={"error": "Unsupported media type"}
                    )
            
            # Validate request size
            if not await self._validate_request_size(request):
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request entity too large"}
                )
            
            # Validate and sanitize request data
            sanitized_request = await self._validate_and_sanitize_request(request)
            if sanitized_request is None:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid or malicious input detected"}
                )
            
            # Process the request
            response = await call_next(sanitized_request)
            
            # Add security headers to response
            return self._add_security_headers(response)
            
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal security error"}
            )
    
    def _validate_http_method(self, request: Request) -> bool:
        """Validate HTTP method"""
        allowed_methods = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'}
        return request.method in allowed_methods
    
    def _validate_content_type(self, request: Request) -> bool:
        """Validate content type for requests with body"""
        content_type = request.headers.get('content-type', '').lower()
        
        # Extract base content type (ignore charset, boundary, etc.)
        base_content_type = content_type.split(';')[0].strip()
        
        return base_content_type in self.allowed_content_types
    
    async def _validate_request_size(self, request: Request) -> bool:
        """Validate request size"""
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                max_size = 50 * 1024 * 1024  # 50MB max request size
                return size <= max_size
            except ValueError:
                return False
        return True
    
    async def _validate_and_sanitize_request(self, request: Request) -> Optional[Request]:
        """Validate and sanitize request data"""
        try:
            # Validate URL path
            if not self._validate_path(request.url.path):
                logger.warning(f"Path traversal attempt detected: {request.url.path}")
                return None
            
            # Validate query parameters
            if not self._validate_query_params(dict(request.query_params)):
                logger.warning(f"Malicious query parameters detected: {request.query_params}")
                return None
            
            # Validate headers
            if not self._validate_headers(dict(request.headers)):
                logger.warning(f"Malicious headers detected")
                return None
            
            # For requests with body, validate and sanitize the content
            if request.method in ['POST', 'PUT', 'PATCH']:
                content_type = request.headers.get('content-type', '').lower()
                
                if 'application/json' in content_type:
                    try:
                        body = await request.body()
                        if body:
                            json_data = json.loads(body)
                            if not self._validate_json_data(json_data):
                                return None
                            
                            # Sanitize JSON data
                            sanitized_data = self._sanitize_json_data(json_data)
                            
                            # Create new request with sanitized data
                            sanitized_body = json.dumps(sanitized_data).encode()
                            request._body = sanitized_body
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON in request body")
                        return None
                    except Exception as e:
                        logger.error(f"Error processing JSON body: {str(e)}")
                        return None
            
            return request
            
        except Exception as e:
            logger.error(f"Error validating request: {str(e)}")
            return None
    
    def _validate_path(self, path: str) -> bool:
        """Validate URL path for path traversal attacks"""
        for pattern in self.compiled_path_patterns:
            if pattern.search(path):
                return False
        return True
    
    def _validate_query_params(self, params: Dict[str, str]) -> bool:
        """Validate query parameters"""
        for key, value in params.items():
            if not self._validate_string_input(key) or not self._validate_string_input(value):
                return False
        return True
    
    def _validate_headers(self, headers: Dict[str, str]) -> bool:
        """Validate request headers"""
        dangerous_headers = ['x-forwarded-host', 'x-original-url', 'x-rewrite-url']
        
        # Headers that should be excluded from SQL injection pattern checks
        safe_headers = {
            'accept', 'accept-encoding', 'accept-language', 'content-type',
            'user-agent', 'referer', 'origin', 'host', 'connection',
            'cache-control', 'pragma', 'authorization', 'cookie',
            'access-control-request-method', 'access-control-request-headers'
        }
        
        for header_name, header_value in headers.items():
            header_name_lower = header_name.lower()
            
            # Check for dangerous headers
            if header_name_lower in dangerous_headers:
                return False
            
            # Skip SQL injection validation for safe headers that commonly contain special characters
            if header_name_lower in safe_headers:
                # Only do basic validation for safe headers
                if len(header_value) > 10000:  # Prevent excessively long headers
                    return False
                continue
            
            # Validate header values for custom headers only
            if not self._validate_string_input(header_value):
                return False
        
        return True
    
    def _validate_json_data(self, data: Any) -> bool:
        """Recursively validate JSON data"""
        if isinstance(data, dict):
            for key, value in data.items():
                if not self._validate_string_input(str(key)):
                    return False
                if not self._validate_json_data(value):
                    return False
        elif isinstance(data, list):
            for item in data:
                if not self._validate_json_data(item):
                    return False
        elif isinstance(data, str):
            if not self._validate_string_input(data):
                return False
        
        return True
    
    def _validate_string_input(self, input_str: str) -> bool:
        """Validate string input for various attack patterns"""
        if not isinstance(input_str, str):
            return True
        
        # Check for SQL injection patterns
        for pattern in self.compiled_sql_patterns:
            if pattern.search(input_str):
                logger.warning(f"SQL injection pattern detected: {input_str[:100]}")
                return False
        
        # Check for XSS patterns
        for pattern in self.compiled_xss_patterns:
            if pattern.search(input_str):
                logger.warning(f"XSS pattern detected: {input_str[:100]}")
                return False
        
        # Check for excessively long strings (potential DoS)
        if len(input_str) > 10000:  # 10KB limit for individual strings
            logger.warning(f"Excessively long string detected: {len(input_str)} characters")
            return False
        
        return True
    
    def _sanitize_json_data(self, data: Any) -> Any:
        """Recursively sanitize JSON data"""
        if isinstance(data, dict):
            return {key: self._sanitize_json_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_json_data(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data
    
    def _sanitize_string(self, input_str: str) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            return input_str
        
        # HTML escape to prevent XSS
        sanitized = html.escape(input_str)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Limit string length
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000]
        
        return sanitized
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip.strip()
        
        # Fallback to client host
        return request.client.host if request.client else 'unknown'
    
    def _is_allowed_ip(self, ip_address: str) -> bool:
        """Check if IP address is allowed based on whitelist/blacklist"""
        # If whitelist is configured, only allow whitelisted IPs
        if self.ip_whitelist:
            return ip_address in self.ip_whitelist
        
        # If blacklist is configured, block blacklisted IPs
        if self.ip_blacklist:
            return ip_address not in self.ip_blacklist
        
        # If no lists configured, allow all IPs
        return True
    
    def _is_safe_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is safe (not a blocked bot)"""
        if not user_agent:
            return False
        
        user_agent_lower = user_agent.lower()
        for blocked_agent in self.blocked_user_agents:
            if blocked_agent in user_agent_lower:
                return False
        
        return True
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add comprehensive security headers to response"""
        # Use security headers from config
        security_headers = get_security_headers()
        
        # Add headers to response
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware with multiple strategies"""
    
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis_client = redis_client
        self.memory_store = {}  # Fallback to memory if Redis unavailable
        
        # Import rate limit configurations from security config
        from ..config.security import get_rate_limit_config, get_endpoint_rate_limit_mapping
        
        # Rate limit configurations from security config
        self.rate_limits = get_rate_limit_config()
        
        # Endpoints and their rate limit categories from security config
        self.endpoint_categories = get_endpoint_rate_limit_mapping()
        
        # Burst protection - track rapid successive requests
        self.burst_threshold = 10  # Max requests in 10 seconds
        self.burst_window = 10
        
        # Progressive penalties for repeat offenders
        self.penalty_multipliers = {
            1: 1.0,    # First offense - normal rate limit
            2: 2.0,    # Second offense - 2x penalty
            3: 4.0,    # Third offense - 4x penalty
            4: 8.0,    # Fourth+ offense - 8x penalty
        }
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting based on endpoint and client"""
        try:
            # Skip rate limiting for health checks
            if request.url.path in ['/', '/health', '/health/', '/metrics', '/docs', '/openapi.json']:
                return await call_next(request)
            
            # Get client identifier
            client_id = self._get_client_identifier(request)
            
            # Determine rate limit category
            category = self._get_rate_limit_category(request.url.path)
            
            # Check rate limit
            if not await self._check_rate_limit(client_id, category):
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": self.rate_limits[category]['window']
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            limit_info = await self._get_rate_limit_info(client_id, category)
            response.headers['X-RateLimit-Limit'] = str(self.rate_limits[category]['requests'])
            response.headers['X-RateLimit-Remaining'] = str(limit_info['remaining'])
            response.headers['X-RateLimit-Reset'] = str(limit_info['reset_time'])
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limit middleware error: {str(e)}")
            # If rate limiting fails, allow the request to proceed
            return await call_next(request)
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier for rate limiting"""
        # Try to get user ID from JWT token
        auth_header = request.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                from ..services.auth_service import AuthService
                from ..database import get_db
                
                # This is a simplified approach - in production you'd want to cache this
                token = auth_header.replace('Bearer ', '')
                # For now, use a hash of the token as identifier
                import hashlib
                return hashlib.sha256(token.encode()).hexdigest()[:16]
            except:
                pass
        
        # Fallback to IP address
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        return request.client.host if request.client else 'unknown'
    
    def _get_rate_limit_category(self, path: str) -> str:
        """Determine rate limit category based on endpoint path"""
        for endpoint_prefix, category in self.endpoint_categories.items():
            if path.startswith(endpoint_prefix):
                return category
        return 'default'
    
    async def _check_rate_limit(self, client_id: str, category: str) -> bool:
        """Check if client has exceeded rate limit"""
        config = self.rate_limits[category]
        current_time = int(time.time())
        window_start = current_time - config['window']
        
        key = f"rate_limit:{category}:{client_id}"
        
        try:
            if self.redis_client:
                # Use Redis for distributed rate limiting
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                pipe.zadd(key, {str(current_time): current_time})
                pipe.expire(key, config['window'])
                results = pipe.execute()
                
                current_requests = results[1]
                return current_requests < config['requests']
            else:
                # Fallback to memory store
                if key not in self.memory_store:
                    self.memory_store[key] = []
                
                # Clean old entries
                self.memory_store[key] = [
                    timestamp for timestamp in self.memory_store[key]
                    if timestamp > window_start
                ]
                
                # Check limit
                if len(self.memory_store[key]) >= config['requests']:
                    return False
                
                # Add current request
                self.memory_store[key].append(current_time)
                return True
                
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            # If rate limiting fails, allow the request
            return True
    
    async def _get_rate_limit_info(self, client_id: str, category: str) -> Dict[str, int]:
        """Get current rate limit information for client"""
        config = self.rate_limits[category]
        current_time = int(time.time())
        window_start = current_time - config['window']
        
        key = f"rate_limit:{category}:{client_id}"
        
        try:
            if self.redis_client:
                current_requests = self.redis_client.zcard(key)
            else:
                if key not in self.memory_store:
                    current_requests = 0
                else:
                    # Clean old entries
                    self.memory_store[key] = [
                        timestamp for timestamp in self.memory_store[key]
                        if timestamp > window_start
                    ]
                    current_requests = len(self.memory_store[key])
            
            return {
                'remaining': max(0, config['requests'] - current_requests),
                'reset_time': window_start + config['window']
            }
            
        except Exception as e:
            logger.error(f"Rate limit info error: {str(e)}")
            return {
                'remaining': config['requests'],
                'reset_time': current_time + config['window']
            }