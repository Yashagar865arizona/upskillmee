import os
import sys
import uuid
import re
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, cast

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Common imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

# Import the app module correctly - always use relative imports from backend directory
from app.routers import auth_router, chat_router, user_router, learning_router, embedding_router, memory_router
from app.config.settings import settings
from app.database.database import SessionLocal, engine, AsyncSessionLocal
from app.database import get_db
from app.models.user import User
from app.models.chat import Message, Conversation
from app.services.message_service import MessageService
from app.services.user_service import UserService
from app.services.ai_integration_service import AIIntegrationService
# from app.services.websocket_handler import WebSocketHandler  # Not currently used
from app.services.learning_service import LearningService
from app.services.embedding_service import EmbeddingService
from app.database import Base

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Set auth_router logger to DEBUG
logging.getLogger("app.routers.auth_router").setLevel(logging.DEBUG)
logging.getLogger("app.services.auth_service").setLevel(logging.DEBUG)

app = FastAPI(
    title="Ponder API",
    description="API for Ponder - An AI-powered learning platform",
    version="1.0.0"
)
logger = logging.getLogger(__name__)

# Debug auth configuration
logger.debug(f"JWT_SECRET: {settings.JWT_SECRET[:5]}..." if settings.JWT_SECRET and len(settings.JWT_SECRET) > 5 else "JWT_SECRET not set!")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API version prefix
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(user_router, prefix="/api/v1/users", tags=["users"])
app.include_router(learning_router, prefix="/api/v1/learning", tags=["learning"])
app.include_router(embedding_router, prefix="/api/v1/embedding", tags=["embedding"])
app.include_router(memory_router, prefix="/api/v1/memory", tags=["memory"])
logger.info(f"ENVIRONMENT: {settings.ENVIRONMENT}")
logger.info(f"OPENAI_API_KEY Loaded: {'Yes' if settings.OPENAI_API_KEY else 'No'}")
logger.info(f"JWT_SECRET Loaded: {'Yes' if settings.JWT_SECRET else 'No'}")

# Create database tables
Base.metadata.create_all(bind=engine)

@app.get('/')
async def health_check():
    return {'status': 'ok'}

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        logger.info("ConnectionManager initialized")

    async def connect(self, websocket: WebSocket):
        logger.info(f"New WebSocket connection request from {websocket.client}")
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connection accepted. Total active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        logger.info(f"Disconnecting WebSocket from {websocket.client}")
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Remaining active connections: {len(self.active_connections)}")
        else:
            logger.warning(f"Attempted to disconnect a WebSocket that was not in active_connections")

manager = ConnectionManager()

@app.websocket("/api/v1/chat/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logger.debug("WebSocket connected")
    try:
        # Get database session
        db = next(get_db())
        
        # Initialize services
        message_service = MessageService(db=db)
        user_service = UserService(message_service=message_service)
        ai_service = AIIntegrationService()
        learning_service = LearningService(openai_api_key=settings.OPENAI_API_KEY)
        
        # Initialize embedding service
        try:
            embedding_service = EmbeddingService(db=db)
            logger.info("Embedding service initialized")
        except Exception as e:
            logger.error(f"Error initializing embedding service: {str(e)}", exc_info=True)
            embedding_service = None
            
        # WebSocket handler initialization (currently not used in this implementation)
        # async with AsyncSessionLocal() as async_db:
        #     websocket_handler = WebSocketHandler(db=async_db)
            
            # Get initial data
            data = await websocket.receive_json()
            
            # Extract token if available
            token = data.get("token")
            
            # Get user ID from token if available
            user_id = None
            user = None
            
            if token:
                try:
                    # Verify token and get user
                    user = db.query(User).filter(User.id == user_id).first()
                    if not user:
                        logger.warning("User not found")
                        await websocket.send_json({
                            "error": "Authentication failed",
                            "message": "User not found"
                        })
                        return
                        
                except Exception as e:
                    logger.error(f"Error verifying token: {str(e)}")
                    await websocket.send_json({
                        "error": "Authentication error",
                        "message": str(e)
                    })
                    return
            
            # Process messages
            while True:
                try:
                    data = await websocket.receive_json()
                    message_data = {
                        "content": data.get("message", ""),
                        "user_id": user_id,
                        "conversation_id": data.get("conversation_id"),
                        "type": data.get("type", "message")
                    }
                    
                    # Process the message
                    response = await message_service.process_message(message_data)
                    
                    # Send response back to client
                    await websocket.send_json(response)
                    
                except WebSocketDisconnect:
                    manager.disconnect(websocket)
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    await websocket.send_json({
                        "error": "An error occurred while processing your message",
                        "details": str(e)
                    })
                    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)
