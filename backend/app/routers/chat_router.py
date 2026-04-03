"""
Location: upskillmee/backend/app/routers/chat_router.py

This module implements the chat routing functionality for the FastAPI backend.
Key features:
- Handles incoming chat messages from clients
- Processes messages through the MessageService 
- Supports both HTTP and WebSocket communication
- Manages conversation history and feedback
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, Request, BackgroundTasks, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import logging
import json
import time
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator

from ..database import get_db
from ..services.message_service import MessageService
from ..config import settings
from ..monitoring.metrics import ai_metrics
from ..models.chat import Message, Conversation
from ..models.project import Project
from ..schemas.validation import SecureChatMessage, SecureStringField, UUIDField
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class FileAttachment(BaseModel):
    """File attachment model"""
    id: str
    name: SecureStringField = Field(..., max_length=255)
    size: int = Field(..., ge=0, le=50*1024*1024)  # Max 50MB
    type: SecureStringField = Field(..., max_length=100)
    content: Optional[str] = None  # For text files
    preview: Optional[str] = None  # For image previews

class ChatMessage(SecureChatMessage):
    """Enhanced chat message model with security validation"""
    files: Optional[List[FileAttachment]] = None
    typing_indicator: Optional[bool] = False

class ChatResponse(BaseModel):
    """Standard response model for chat endpoints"""
    id: str
    text: str
    conversation_id: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class FeedbackRequest(BaseModel):
    """Feedback data for messages"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    useful: Optional[bool] = None
    comments: Optional[SecureStringField] = Field(None, max_length=1000)
    tags: Optional[List[SecureStringField]] = None
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 10:  # Limit number of tags
                raise ValueError("Too many tags")
            for tag in v:
                if len(tag) > 50:  # Limit individual tag length
                    raise ValueError("Tag too long")
        return v

def get_message_service(db: Session = Depends(get_db)) -> MessageService:
    """Get an instance of the message service"""
    return MessageService(db)

# Create a class-based router for backward compatibility
class ChatRouter:
    def __init__(self):
        self.router = APIRouter()
        self._setup_routes()
        
    def _setup_routes(self):
        # Register all routes on the router
        self.router.add_api_route("/message", self.process_message, methods=["POST"], response_model=ChatResponse)
        self.router.add_api_route("/stream", self.stream_message, methods=["POST"])
        self.router.add_api_route("/history/{user_id}", self.get_chat_history, methods=["GET"])
        self.router.add_api_route("/feedback/{message_id}", self.save_feedback, methods=["POST"])
        self.router.add_websocket_route("/ws", self.websocket_endpoint)

    async def process_message(
        self,
        message_data: ChatMessage,
        background_tasks: BackgroundTasks,
        message_service: MessageService = Depends(get_message_service)
    ) -> Dict[str, Any]:
        """
        Process a chat message and return a response.
        This is the main endpoint for chat functionality.
        """
        try:
            # Process the message using the message service
            response = await message_service.process_message(message_data.dict())
            return response
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def stream_message(
        self,
        message_data: ChatMessage,
        background_tasks: BackgroundTasks,
        message_service: MessageService = Depends(get_message_service)
    ) -> StreamingResponse:
        """Stream a chat response for real-time interaction"""
        try:
            async def generate() -> AsyncGenerator[str, None]:
                # Process the message
                response = await message_service.process_message(message_data.dict())
                
                # Stream the response
                if isinstance(response, dict):
                    yield f"data: {json.dumps(response)}\n\n"
                else:
                    yield f"data: {json.dumps({'text': str(response)})}\n\n"
                
                # Signal completion
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        except Exception as e:
            logger.error(f"Error streaming message: {str(e)}")
            return StreamingResponse(
                iter([f"data: {json.dumps({'error': str(e)})}\n\n"]),
                media_type="text/event-stream"
            )

    async def get_chat_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """Get chat history for a user with pagination"""
        try:
            # Query messages with pagination
            messages = db.query(Message)\
                .filter(Message.user_id == user_id)\
                .order_by(Message.created_at.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            # Count total messages for pagination
            total_count = db.query(Message)\
                .filter(Message.user_id == user_id)\
                .count()
            
            # Get conversation IDs for grouping
            conversation_ids = set(msg.conversation_id for msg in messages if msg.conversation_id)
            
            # Get conversation data
            conversations = {}
            if conversation_ids:
                conversation_records = db.query(Conversation)\
                    .filter(Conversation.id.in_(conversation_ids))\
                    .all()
                conversations = {conv.id: conv.to_dict() for conv in conversation_records}
            
            return {
                "messages": [msg.to_dict() for msg in messages],
                "conversations": conversations,
                "pagination": {
                    "total": total_count,
                    "offset": offset,
                    "limit": limit
                }
            }
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def save_feedback(
        self,
        message_id: str,
        feedback: FeedbackRequest,
        db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """Save user feedback for a message"""
        try:
            # Find the message
            message = db.query(Message).filter(Message.id == message_id).first()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")
            
            # Update the feedback
            feedback_data = feedback.dict(exclude_none=True)
            
            # Merge with existing feedback if any
            existing_feedback = message.feedback or {}
            updated_feedback = {**existing_feedback, **feedback_data}
            
            # Update the message
            db.query(Message).filter(Message.id == message_id).update({
                Message.feedback: updated_feedback,
                Message.updated_at: datetime.now(timezone.utc)
            })
            db.commit()
            
            return {"status": "success", "message": "Feedback saved successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving feedback: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def websocket_endpoint(
        self,
        websocket: WebSocket,
        db: Session = Depends(get_db)
    ) -> None:
        """WebSocket endpoint for real-time chat with enhanced features"""
        await websocket.accept()
        user_id = None
        
        try:
            message_service = MessageService(db)
            
            while True:
                # Receive message
                data = await websocket.receive_text()
                
                try:
                    # Parse the message
                    message_data = json.loads(data)
                    
                    # Handle different message types
                    if message_data.get('type') == 'auth':
                        # Handle authentication
                        token = message_data.get('token')
                        if token:
                            # Verify token and extract user_id
                            # This would typically involve JWT verification
                            user_id = message_data.get('user_id')  # Simplified for now
                            await websocket.send_json({
                                "status": "acknowledged",
                                "message": "Authentication successful"
                            })
                        else:
                            await websocket.send_json({
                                "error": "Authentication required",
                                "auth_required": True
                            })
                        continue
                    
                    elif message_data.get('type') == 'heartbeat':
                        # Handle heartbeat
                        await websocket.send_json({"type": "heartbeat_ack"})
                        continue
                    
                    elif message_data.get('type') == 'typing':
                        # Handle typing indicator
                        # Broadcast to other users in conversation if needed
                        await websocket.send_json({
                            "type": "typing_indicator",
                            "user_id": user_id,
                            "is_typing": message_data.get('is_typing', False)
                        })
                        continue
                    
                    elif message_data.get('type') == 'message':
                        # Handle chat message with potential file attachments
                        if not user_id:
                            await websocket.send_json({
                                "error": "Authentication required",
                                "auth_required": True
                            })
                            continue
                        
                        # Add user_id to message data
                        message_data['user_id'] = user_id
                        
                        # Process files if present
                        if message_data.get('files'):
                            processed_files = []
                            for file_data in message_data['files']:
                                # Validate and process file
                                if self._validate_file(file_data):
                                    processed_files.append(file_data)
                            message_data['files'] = processed_files
                        
                        # Process the message
                        response = await message_service.process_message(message_data)
                        
                        # Send the response
                        await websocket.send_json(response)
                    
                    else:
                        await websocket.send_json({"error": "Unknown message type"})
                        
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                    await websocket.send_json({"error": "Invalid message format"})
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {str(e)}")
                    await websocket.send_json({"error": str(e)})
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user: {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            try:
                await websocket.close()
            except:
                pass

    def _validate_file(self, file_data: dict) -> bool:
        """Validate uploaded file data"""
        try:
            # Check file size (max 50MB)
            if file_data.get('size', 0) > 50 * 1024 * 1024:
                return False
            
            # Check file type
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'text/plain', 'text/markdown', 'text/csv',
                'application/pdf', 'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            
            if file_data.get('type') not in allowed_types:
                return False
            
            # Check filename
            filename = file_data.get('name', '')
            if not filename or len(filename) > 255:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return False

# Create and export the router object with backward compatibility structure
router = ChatRouter()