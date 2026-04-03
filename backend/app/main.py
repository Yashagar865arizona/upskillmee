"""
Main FastAPI application module.
"""

from fastapi import FastAPI
from app.config.env import load_environment

# Load environment variables before anything else
environment = load_environment()

from fastapi import FastAPI, HTTPException, Request, WebSocket, Depends
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import uuid
import psutil
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocketDisconnect
from .middleware.analytics_middleware import AnalyticsMiddleware
from .middleware.monitoring_middleware import MonitoringMiddleware, HealthCheckMiddleware
from .middleware.security_middleware import SecurityMiddleware, RateLimitMiddleware
import traceback
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import json
import asyncio
import openai
from jose import jwt, JWTError
import time
import os
from fastapi.staticfiles import StaticFiles
from app.routers.user_router import user_router
# Import configuration first
from .config.settings import settings
from .services.auth_service import AuthService

# Import database components after config
from .database import engine, get_db
from .database.base import Base

# Import models
from .models import User, UserProfile, UserProject, UserSnapshot, Conversation, Message, TokenBlacklist  # noqa

# Import services
from .services.message_service import MessageService

# Import API routers - using the api directory for core system endpoints
from .api.health import health_router
from .api.metrics import metrics_router
from .api.admin import admin_router
from .api.monitoring import router as monitoring_router
from .api.production_monitoring import router as production_monitoring_router
from app.routers.document_router import router as document_router
from app.routers.feedback_router import router as feedback_router
from starlette.middleware.sessions import SessionMiddleware
# Import feature routers - simplified using the routers package exports
from .routers import (
    auth_router,
    chat_router,
    learning_router,
    memory_router,
    embedding_router
)
from .routers.user_projects_router import router as user_projects_router
from .routers.analytics_router import router as analytics_router
from .routers.assessment_router import router as assessment_router
from .routers.session_router import router as session_router
from .routers.discovery_report_router import router as discovery_report_router
from .routers.skill_map_router import router as skill_map_router
from .routers.portfolio_router import router as portfolio_router
from .routers.referral_router import router as referral_router

# Configure logging
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# Reduce SQL logging noise
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('uvicorn').setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Optimized lifespan context manager for startup and shutdown events"""
    from .services.startup_optimization_service import startup_service, ServiceConfig, ServicePriority
    
    # Register all services for optimized initialization
    await register_startup_services(startup_service)
    
    # Initialize all services in optimal order
    services = await startup_service.initialize_services()
    
    # Optimize memory usage after startup
    startup_service.optimize_memory_usage()
    
    # Log startup metrics
    metrics = startup_service.get_startup_metrics()
    logger.info(f"Startup completed - Total time: {metrics.get('total_startup_time', 0):.2f}s")
    
    yield
    
    # Graceful shutdown
    await startup_service.graceful_shutdown()

async def register_startup_services(startup_service):
    """Register all services with the startup optimization service"""
    from .services.startup_optimization_service import ServiceConfig, ServicePriority
    
    # Critical services (must be initialized first)
    startup_service.register_service(ServiceConfig(
        name="directories",
        init_func=initialize_directories,
        priority=ServicePriority.CRITICAL,
        timeout=10.0
    ))
    
    startup_service.register_service(ServiceConfig(
        name="database",
        init_func=initialize_database,
        priority=ServicePriority.CRITICAL,
        timeout=30.0,
        dependencies=["directories"],
        health_check=check_database_health
    ))
    
    # High priority services
    startup_service.register_service(ServiceConfig(
        name="database_monitoring",
        init_func=initialize_database_monitoring_service,
        priority=ServicePriority.HIGH,
        timeout=15.0,
        dependencies=["database"]
    ))
    
    startup_service.register_service(ServiceConfig(
        name="enhanced_db_monitoring",
        init_func=initialize_enhanced_db_monitoring_service,
        priority=ServicePriority.HIGH,
        timeout=15.0,
        dependencies=["database"]
    ))
    
    # Medium priority services
    startup_service.register_service(ServiceConfig(
        name="redis_connection",
        init_func=initialize_redis_connection,
        priority=ServicePriority.MEDIUM,
        timeout=10.0,
        health_check=check_redis_health
    ))
    
    startup_service.register_service(ServiceConfig(
        name="resource_optimization",
        init_func=initialize_resource_optimization,
        priority=ServicePriority.MEDIUM,
        timeout=10.0,
        cleanup_func=cleanup_resource_optimization
    ))
    
    # Background services
    startup_service.register_service(ServiceConfig(
        name="production_monitoring",
        init_func=initialize_production_monitoring,
        priority=ServicePriority.BACKGROUND,
        timeout=20.0,
        cleanup_func=cleanup_production_monitoring
    ))

# Service initialization functions
async def initialize_directories():
    """Initialize required directories"""
    from .services.data_management_service import DataManagementService
    data_service = DataManagementService()
    data_service._ensure_directories()
    logger.info("Required directories initialized")
    return data_service

async def initialize_database():
    """Initialize database with optimized connection pooling"""
    from sqlalchemy import text
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Warm up connection pool
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    
    logger.info("Database initialized with connection pool warmed up")
    return engine

async def check_database_health():
    """Check database connectivity"""
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        if result != 1:
            raise RuntimeError("Database health check failed")

async def initialize_database_monitoring_service():
    """Initialize database monitoring for query performance optimization"""
    from .services.database_monitoring import initialize_database_monitoring
    initialize_database_monitoring(engine)
    logger.info("Database monitoring initialized for query performance optimization")
    return True

async def initialize_enhanced_db_monitoring_service():
    """Initialize enhanced database monitoring"""
    from .services.enhanced_db_monitoring import initialize_enhanced_db_monitoring
    initialize_enhanced_db_monitoring()
    logger.info("Enhanced database monitoring initialized")
    return True

async def initialize_redis_connection():
    """Initialize Redis connection with health check"""
    global redis_client
    if redis_client:
        try:
            redis_client.ping()
            logger.info("Redis connection verified")
            return redis_client
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            redis_client = None
    return None

async def check_redis_health():
    """Check Redis connectivity"""
    if redis_client:
        redis_client.ping()

async def initialize_production_monitoring():
    """Initialize production monitoring background tasks"""
    try:
        from .services.backup_monitoring_service import backup_monitoring
        
        # Start backup monitoring
        task = asyncio.create_task(backup_monitoring.schedule_backup_monitoring())
        logger.info("Production monitoring services started")
        return task
        
    except Exception as e:
        logger.error(f"Failed to start production monitoring: {e}")
        return None

async def initialize_resource_optimization():
    """Initialize resource optimization service"""
    from .services.resource_optimization_service import resource_optimizer, memory_optimizer
    
    # Set thresholds based on environment
    if settings.ENVIRONMENT == "production":
        resource_optimizer.set_memory_threshold(1024)  # 1GB in production
        resource_optimizer.set_cpu_threshold(85.0)
    else:
        resource_optimizer.set_memory_threshold(512)   # 512MB in development
        resource_optimizer.set_cpu_threshold(90.0)
    
    # Register cache clearing functions
    try:
        # Register any application caches here
        pass
    except Exception as e:
        logger.warning(f"Could not register cache clearing functions: {e}")
    
    # Start monitoring
    await resource_optimizer.start_monitoring(interval=120)  # Monitor every 2 minutes
    logger.info("Resource optimization service initialized")
    return resource_optimizer

async def cleanup_resource_optimization():
    """Cleanup resource optimization service"""
    from .services.resource_optimization_service import resource_optimizer
    await resource_optimizer.stop_monitoring()
    logger.info("Resource optimization service cleanup completed")

async def cleanup_production_monitoring():
    """Cleanup production monitoring tasks"""
    # Cancel any running monitoring tasks
    tasks = [task for task in asyncio.all_tasks() if task.get_name().startswith('backup_monitoring')]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    logger.info("Production monitoring cleanup completed")

# Create FastAPI app
app = FastAPI(
    title="upskillmee API",
    description="Backend API for upskillmee learning platform",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key",
    session_cookie="upskillmee_session",
    same_site="lax",  # change from "none"
    https_only=False,  # ok for localhost
)


# Include all routers with non-versioned paths for backward compatibility
# These routes are still being used by the frontend
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(learning_router, prefix="/learning", tags=["learning"])
app.include_router(memory_router, prefix="/memory", tags=["memory"])
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(embedding_router, prefix="/embeddings", tags=["embeddings"])
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(metrics_router, prefix="/metrics", tags=["metrics"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(document_router,prefix="/documents", tags=["Documents"])
app.include_router(feedback_router,prefix="/feedback", tags=["Feedback"])
app.include_router(session_router)  # prefix already set in router (/api/sessions)
# Note: The versioned API routes (/api/v1/...) are registered at the bottom of the file


app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/test")
def test_endpoint():

    return {"message": "Hello, world!"}

# Add a basic root endpoint for quick testing
@app.get("/", tags=["root"])
async def root():
    return {"message": "upskillmee API is up and running!"}

# Import security configuration
from .config.security import (
    get_cors_origins, get_allowed_methods, get_allowed_headers,
    get_exposed_headers, security_config
)

# Enhanced CORS configuration using security config
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=security_config.CORS_ALLOW_CREDENTIALS,
    allow_methods=get_allowed_methods(),
    allow_headers=get_allowed_headers(),
    expose_headers=get_exposed_headers(),
    max_age=security_config.CORS_MAX_AGE,
)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        return response

# Initialize Redis for rate limiting
redis_client = None
try:
    import redis
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    # Test Redis connection
    redis_client.ping()
    logger.info("Redis connection established for rate limiting")
except Exception as e:
    logger.warning(f"Redis not available for rate limiting, falling back to memory: {str(e)}")
    redis_client = None

# Add middleware in correct order (last added = first executed)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(RateLimitMiddleware, redis_client=redis_client)
app.add_middleware(AnalyticsMiddleware)
app.add_middleware(MonitoringMiddleware)
app.add_middleware(HealthCheckMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests",
            "retry_after": getattr(exc, 'retry_after', 30)
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())
    
    # Track the error in monitoring system
    from .services.monitoring_service import monitoring_service
    monitoring_service.error_tracker.track_error(exc, {
        "error_id": error_id,
        "endpoint": request.url.path,
        "method": request.method,
        "user_agent": request.headers.get("user-agent"),
        "ip_address": request.client.host if request.client else None
    })
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "error_id": error_id}
        )
    else:
        logger.error(f"Unhandled exception {error_id}: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred",
                "error_id": error_id
            }
        )

# Service dependencies
def get_message_service(db: Session = Depends(get_db)):
    return MessageService(db=db)

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        # Safely remove the websocket if it exists in the list
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

manager = ConnectionManager()

@app.websocket("/api/v1/chat/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Use synchronous database session
        db = next(get_db())
        message_service = MessageService(db)

        # Store user_id for this connection
        user_id = None

        while True:
            try:
                # Receive and parse message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                # Skip processing for heartbeat messages
                if message_data.get('type') == 'heartbeat':
                    await websocket.send_json({"type": "heartbeat_ack"})
                    continue

                # For auth messages, extract user_id from token and store it
                if message_data.get('type') == 'auth':
                    token = message_data.get('token')
                    if token:
                        try:
                            # Create auth service
                            auth_service = AuthService(db)

                            # Extract user_id from token
                            payload = auth_service.decode_token(token)
                            if payload and "sub" in payload:
                                user_id = payload["sub"]
                                # Store user_id for this connection
                                # user_id is already set from payload["sub"]
                                logger.info(f"Auth message received with valid token for user {user_id}")
                            else:
                                logger.warning("Auth message received with invalid token")
                        except Exception as e:
                            logger.error(f"Error extracting user_id from token: {str(e)}")

                    await websocket.send_json({"status": "acknowledged", "type": "system"})
                    continue

                # Process message with timeout protection
                try:
                    # For non-auth messages, ensure user_id is set
                    if message_data.get('type') != 'auth' and message_data.get('type') != 'heartbeat':
                        if not user_id:
                            # If no user_id is available, send auth required message
                            await websocket.send_json({
                                "text": "Authentication required. Please log in to continue.",
                                "sender": "bot",
                                "id": str(uuid.uuid4()),
                                "auth_required": True
                            })
                            continue

                        # Process the actual message
                        user_message = message_data.get('message', '')
                        if user_message:
                            start_time = time.time()  # Track processing start time
                            logger.info(f"Processing message from user {user_id}: {user_message[:50]}...")

                            # Get user from database
                            user = db.query(User).filter(User.id == user_id).first()
                            if not user:
                                logger.error(f"User {user_id} not found in database")
                                await websocket.send_json({
                                    "text": "User not found. Please try logging in again.",
                                    "sender": "bot",
                                    "id": str(uuid.uuid4())
                                })
                                continue

                            # CRITICAL FIX: Set the current user in message service for memory system
                            message_service.set_current_user(user)
                            logger.info(f"MEMORY: Set current user {user.id} in message service for memory system")

                            # Process message and get AI response
                            try:
                                # Get or create conversation for this user
                                conversation = db.query(Conversation).filter(
                                    Conversation.user_id == str(user.id),
                                    Conversation.status == 'active'
                                ).order_by(Conversation.updated_at.desc()).first()

                                if not conversation:
                                    # Create new conversation
                                    conversation = Conversation(
                                        user_id=str(user.id),
                                        title=f"Chat - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
                                        status='active'
                                    )
                                    db.add(conversation)
                                    db.commit()
                                    db.refresh(conversation)
                                    logger.info(f"Created new conversation {conversation.id} for user {user.id}")

                                # Set current conversation in message service
                                message_service.set_current_conversation(conversation)

                                # Save user message to database
                                user_msg = Message(
                                    user_id=str(user.id),
                                    conversation_id=str(conversation.id),
                                    content=user_message,
                                    role='user',
                                    message_metadata={'agent_mode': message_data.get('agent_mode', 'chat')}
                                )
                                db.add(user_msg)
                                db.commit()
                                logger.info(f"Saved user message to database")

                                # Track message sent event
                                from .middleware.analytics_middleware import WebSocketAnalyticsTracker
                                ws_tracker = WebSocketAnalyticsTracker()
                                await ws_tracker.track_message_sent(
                                    db, str(user.id), user_message, 
                                    message_data.get('session_id')
                                )

                                # Prepare message data for processing
                                # Include chat history for context and agent mode
                                chat_history = message_data.get('chat_history', [])
                                agent_mode = message_data.get('agent_mode', 'chat')
                                logger.info(f"Received chat history with {len(chat_history)} messages")
                                logger.info(f"Agent mode: {agent_mode}")

                                process_data = {
                                    'message': user_message,
                                    'user_id': str(user.id),
                                    'chat_history': chat_history,
                                    'agent_mode': agent_mode,
                                    'type': 'message'
                                }

                                # Process the message
                                response = await message_service.process_message(process_data)

                                # Send response back to client
                                if isinstance(response, dict):
                                    # Make sure response has the expected format
                                    if 'text' not in response:
                                        response['text'] = "I'm not sure how to respond to that."
                                    if 'sender' not in response:
                                        response['sender'] = "bot"
                                    if 'id' not in response:
                                        response['id'] = str(uuid.uuid4())

                                    # Save AI response to database
                                    ai_msg = Message(
                                        user_id=str(user.id),
                                        conversation_id=str(conversation.id),
                                        content=response['text'],
                                        role='assistant',
                                        message_metadata={
                                            'agent_mode': agent_mode,
                                            'response_id': response['id']
                                        }
                                    )
                                    db.add(ai_msg)
                                    
                                    # Update conversation timestamp
                                    conversation.updated_at = datetime.now(timezone.utc)
                                    db.commit()
                                    logger.info(f"Saved AI response to database")

                                    await websocket.send_json(response)
                                    
                                    # Track message received event
                                    response_time = time.time() - start_time if 'start_time' in locals() else 0
                                    await ws_tracker.track_message_received(
                                        db, str(user.id), response_time, 
                                        message_data.get('session_id')
                                    )
                                else:
                                    # If response is a string, wrap it in a dict
                                    response_text = str(response)
                                    response_id = str(uuid.uuid4())
                                    
                                    # Save AI response to database
                                    ai_msg = Message(
                                        user_id=str(user.id),
                                        conversation_id=str(conversation.id),
                                        content=response_text,
                                        role='assistant',
                                        message_metadata={
                                            'agent_mode': agent_mode,
                                            'response_id': response_id
                                        }
                                    )
                                    db.add(ai_msg)
                                    
                                    # Update conversation timestamp
                                    conversation.updated_at = datetime.now(timezone.utc)
                                    db.commit()
                                    logger.info(f"Saved AI response to database")

                                    await websocket.send_json({
                                        "text": response_text,
                                        "sender": "bot",
                                        "id": response_id
                                    })

                                logger.info(f"Sent response to user {user_id}")
                            except Exception as e:
                                logger.error(f"Error processing message for user {user_id}: {str(e)}")
                                await websocket.send_json({
                                    "text": "Error processing your message. Please try again.",
                                    "sender": "bot",
                                    "id": str(uuid.uuid4())
                                })

                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    await websocket.send_json({
                        "text": "Error processing message. Please try again.",
                        "sender": "bot",
                        "id": str(uuid.uuid4())
                    })

            except WebSocketDisconnect:
                manager.disconnect(websocket)
                break
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                break

    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        manager.disconnect(websocket)
print("ENVIRONMENT:::::::::::::::::::::::", settings.ENVIRONMENT)
print("is_production:::::::::::::::::::", settings.is_production)
print("CORS_ORIGINS:::::::::::::::::", settings.CORS_ORIGINS)

# Register routers
# Core system APIs
app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(metrics_router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

# Feature APIs
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(learning_router, prefix="/api/v1/learning", tags=["learning"])
app.include_router(user_router, prefix="/api/v1/users", tags=["users"])
app.include_router(user_projects_router, prefix="/api/v1/users", tags=["user-projects"])
app.include_router(embedding_router, prefix="/api/v1/embedding", tags=["embedding"])
app.include_router(memory_router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["monitoring"])
app.include_router(feedback_router,prefix="/api/v1/feedback", tags=["feedback"])
app.include_router(production_monitoring_router, prefix="/api/v1/production", tags=["production"])
app.include_router(assessment_router, prefix="/api/v1", tags=["assessment"])
app.include_router(discovery_report_router, prefix="/api/v1", tags=["discovery-report"])
app.include_router(skill_map_router, prefix="/api/v1", tags=["skill-map"])
app.include_router(portfolio_router, prefix="/api/v1", tags=["portfolio"])
app.include_router(referral_router, prefix="/api/v1", tags=["referral"])
