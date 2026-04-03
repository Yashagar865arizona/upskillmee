"""
Analytics middleware for automatic event tracking.
Tracks user interactions, API calls, and system events.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import time
import logging
import json
import uuid
from datetime import datetime, timezone

from ..database import get_db
from ..services.analytics_service import AnalyticsService, EventType
from ..services.auth_service import AuthService

logger = logging.getLogger(__name__)

class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track user events and API metrics"""
    
    def __init__(self, app):
        super().__init__(app)
        self.analytics_service = AnalyticsService()
        
        # Define which endpoints should trigger events
        self.event_mappings = {
            "/api/v1/auth/login": EventType.USER_LOGIN,
            "/api/v1/auth/logout": EventType.USER_LOGOUT,
            "/api/v1/chat/message": EventType.MESSAGE_SENT,
            "/api/v1/learning/generate-plan": EventType.LEARNING_PLAN_GENERATED,
            "/api/v1/learning/accept-plan": EventType.LEARNING_PLAN_ACCEPTED,
            "/api/v1/learning/reject-plan": EventType.LEARNING_PLAN_REJECTED,
            "/api/v1/users/projects": EventType.PROJECT_CREATED,
            "/api/v1/users/profile": EventType.PROFILE_UPDATED,
        }
        
        # Endpoints to exclude from tracking
        self.excluded_endpoints = {
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        }

    async def dispatch(self, request: Request, call_next):
        """Process request and track analytics"""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Skip tracking for excluded endpoints
        if any(request.url.path.startswith(excluded) for excluded in self.excluded_endpoints):
            return await call_next(request)
        
        # Get user information if available
        user_id = await self._extract_user_id(request)
        session_id = self._get_session_id(request)
        
        # Get request metadata
        metadata = {
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
            "request_id": request_id
        }
        
        # Process the request
        response = None
        error = None
        try:
            response = await call_next(request)
            
            # Track successful API call
            if user_id:
                await self._track_api_call(
                    request, user_id, session_id, metadata, 
                    response.status_code, time.time() - start_time
                )
            
        except Exception as e:
            error = e
            logger.error(f"Request {request_id} failed: {str(e)}")
            
            # Track error event
            if user_id:
                error_metadata = metadata.copy()
                error_metadata.update({
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time": time.time() - start_time
                })
                
                try:
                    db = next(get_db())
                    await self.analytics_service.track_event(
                        db, user_id, EventType.ERROR_OCCURRED, 
                        error_metadata, session_id,
                        request.client.host if request.client else None,
                        request.headers.get("user-agent")
                    )
                except Exception as track_error:
                    logger.error(f"Failed to track error event: {track_error}")
            
            raise e
        
        # Add response headers
        if response:
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = str(time.time() - start_time)
        
        return response

    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request if authenticated"""
        try:
            # Check for Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            
            # Create a temporary database session to decode token
            db = next(get_db())
            auth_service = AuthService(db)
            
            payload = auth_service.decode_token(token)
            if payload and "sub" in payload:
                return payload["sub"]
                
        except Exception as e:
            logger.debug(f"Could not extract user ID: {e}")
        
        return None

    def _get_session_id(self, request: Request) -> Optional[str]:
        """Extract or generate session ID"""
        # Try to get session ID from headers or cookies
        session_id = request.headers.get("x-session-id")
        if not session_id:
            session_id = request.cookies.get("session_id")
        
        # Generate new session ID if none found
        if not session_id:
            session_id = str(uuid.uuid4())
        
        return session_id

    async def _track_api_call(self, request: Request, user_id: str, session_id: str, 
                            metadata: dict, status_code: int, response_time: float):
        """Track API call event"""
        try:
            db = next(get_db())
            
            # Determine event type based on endpoint
            event_type = self.event_mappings.get(request.url.path)
            
            # If no specific event type, track as general API call
            if not event_type:
                # Don't track every API call to avoid noise
                return
            
            # Add response metadata
            api_metadata = metadata.copy()
            api_metadata.update({
                "status_code": status_code,
                "response_time_seconds": response_time,
                "success": 200 <= status_code < 400
            })
            
            # Track the specific event
            await self.analytics_service.track_event(
                db, user_id, event_type, api_metadata, session_id,
                request.client.host if request.client else None,
                request.headers.get("user-agent")
            )
            
            # Also track session activity
            await self._update_session_activity(db, user_id, session_id, request)
            
        except Exception as e:
            logger.error(f"Failed to track API call: {e}")

    async def _update_session_activity(self, db: Session, user_id: str, 
                                     session_id: str, request: Request):
        """Update session activity metrics"""
        try:
            from ..models.analytics import UserSession
            
            # Get or create session record
            session = db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if not session:
                # Create new session
                session = UserSession(
                    user_id=user_id,
                    session_id=session_id,
                    start_time=datetime.now(timezone.utc),
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    page_views=1,
                    actions_taken=1
                )
                db.add(session)
            else:
                # Update existing session
                session.actions_taken = (session.actions_taken or 0) + 1
                session.end_time = datetime.now(timezone.utc)
                
                # Calculate duration
                if session.start_time:
                    duration = (session.end_time - session.start_time).total_seconds()
                    session.duration_seconds = int(duration)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")
            db.rollback()

class WebSocketAnalyticsTracker:
    """Helper class for tracking WebSocket events"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
    
    async def track_websocket_event(self, db: Session, user_id: str, 
                                  event_type: EventType, metadata: dict = None,
                                  session_id: str = None):
        """Track WebSocket-specific events"""
        try:
            await self.analytics_service.track_event(
                db, user_id, event_type, metadata or {}, session_id
            )
        except Exception as e:
            logger.error(f"Failed to track WebSocket event: {e}")
    
    async def track_message_sent(self, db: Session, user_id: str, 
                               message_content: str, session_id: str = None):
        """Track when user sends a message"""
        metadata = {
            "message_length": len(message_content),
            "has_code": "```" in message_content,
            "has_question": "?" in message_content,
            "word_count": len(message_content.split())
        }
        
        await self.track_websocket_event(
            db, user_id, EventType.MESSAGE_SENT, metadata, session_id
        )
    
    async def track_message_received(self, db: Session, user_id: str,
                                   response_time: float, session_id: str = None):
        """Track when user receives AI response"""
        metadata = {
            "response_time_seconds": response_time,
            "response_speed": "fast" if response_time < 2 else "slow"
        }
        
        await self.track_websocket_event(
            db, user_id, EventType.MESSAGE_RECEIVED, metadata, session_id
        )