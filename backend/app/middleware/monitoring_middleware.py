"""
Monitoring middleware for automatic performance tracking and error monitoring.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
import logging
from typing import Optional

from ..services.monitoring_service import monitoring_service

logger = logging.getLogger(__name__)

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically monitor API performance and errors"""
    
    def __init__(self, app):
        super().__init__(app)
        self.excluded_endpoints = {
            "/health", "/metrics", "/docs", "/openapi.json", "/favicon.ico", "/static"
        }
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        endpoint = request.url.path
        method = request.method

        if any(endpoint.startswith(excluded) for excluded in self.excluded_endpoints):
            return await call_next(request)

        response = None
        error = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error = e
            status_code = 500
            logger.error(f"Request to {method} {endpoint} failed: {str(e)}")
            # Return JSON response instead of re-raising
            response = Response(
                content=f"Internal server error: {str(e)}",
                status_code=500
            )
        finally:
            response_time = time.time() - start_time
            try:
                await monitoring_service.record_api_request(
                    endpoint=endpoint,
                    method=method,
                    response_time=response_time,
                    status_code=status_code,
                    error=error
                )
                if await monitoring_service.should_store_metrics():
                    await monitoring_service.store_metrics_to_database()
            except Exception as storage_error:
                logger.error(f"Failed to store monitoring metrics: {storage_error}")

        return response

class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware to add health check headers to responses"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Add health check headers"""
        response = await call_next(request)
        
        # Add health status header
        try:
            health_status = await monitoring_service.health_checker.run_all_checks()
            response.headers["X-Health-Status"] = health_status["overall_status"]
        except Exception as e:
            logger.error(f"Failed to add health status header: {e}")
            response.headers["X-Health-Status"] = "unknown"
        
        return response