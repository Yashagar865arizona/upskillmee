"""
Location: ponder/backend/app/routers/embedding_router.py

This module implements the embedding functionality for the FastAPI backend.
- Handles storage and retrieval of text embeddings
- Provides statistics on embedding usage
- Manages embedding creation and vector search
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

from ..database import get_db
from ..services.embedding_service import EmbeddingService
from ..monitoring.metrics import embedding_metrics
from ..models.chat import Message

logger = logging.getLogger(__name__)

class EmbeddingRequest(BaseModel):
    """Request model for creating embeddings"""
    text: str
    meta_data: Optional[Dict] = None

class SearchRequest(BaseModel):
    """Request model for searching embeddings"""
    query: str
    limit: int = 5
    min_score: float = 0.7

def get_embedding_service(db: Session = Depends(get_db)) -> EmbeddingService:
    """Get an instance of the embedding service"""
    return EmbeddingService(db=db)

# Create a class-based router for backward compatibility
class EmbeddingRouter:
    def __init__(self):
        self.router = APIRouter()
        self._setup_routes()
        
    def _setup_routes(self):
        # Register all routes on the router
        self.router.add_api_route("/stats", self.get_embedding_stats, methods=["GET"])
        self.router.add_api_route("/create", self.create_embedding, methods=["POST"])
        self.router.add_api_route("/search", self.search_embeddings, methods=["POST"])
    
    async def get_embedding_stats(
        self,
        embedding_service: EmbeddingService = Depends(get_embedding_service),
        db: Session = Depends(get_db)
    ) -> Dict:
        """Get statistics about the embedding storage"""
        try:
            # Get embedding count from database
            total_embeddings = db.query(Message).filter(
                Message.metadata.has_key('embedding')
            ).count()
            
            # Get metric data
            metrics = {
                "total_embeddings": total_embeddings,
                "index_size": getattr(embedding_service, 'index_size', 0),
                "cache_size": getattr(embedding_service, 'cache_size', 0),
                "performance": {
                    "cache_hits": getattr(embedding_metrics, 'cache_hits', 0),
                    "creation_time_avg_ms": getattr(embedding_metrics, 'creation_time_avg_ms', 0),
                    "creation_errors": getattr(embedding_metrics, 'creation_errors', 0)
                }
            }
            
            return metrics
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving embedding stats: {str(e)}")
    
    async def create_embedding(
        self,
        request: EmbeddingRequest,
        embedding_service: EmbeddingService = Depends(get_embedding_service),
        db: Session = Depends(get_db)
    ) -> Dict:
        """Create an embedding for the given text"""
        try:
            # Create the embedding
            embedding = await embedding_service.create_embedding(request.text)
            if embedding is None:
                raise HTTPException(status_code=500, detail="Failed to create embedding")
            
            # Get user_id - in real app would come from auth
            user_id = "system"
            conversation_id = 0  # Default conversation
            
            # Store in database
            message = await embedding_service.store_conversation(
                db=db,
                user_id=user_id,
                text=request.text,
                embedding=embedding,
                conversation_id=conversation_id,
                role="user"
            )
            
            return {
                "id": str(message.id) if message else "unknown",
                "status": "success",
                "message": "Embedding created successfully"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating embedding: {str(e)}")
    
    async def search_embeddings(
        self,
        request: SearchRequest,
        embedding_service: EmbeddingService = Depends(get_embedding_service),
        db: Session = Depends(get_db)
    ) -> Dict:
        """Search for similar embeddings"""
        try:
            # Create an embedding for the query and search for similar content
            query_embedding = await embedding_service.create_embedding(request.query)
            if query_embedding is None:
                raise HTTPException(status_code=500, detail="Failed to create embedding")
            
            # Use the same user_id for all searches in this example
            user_id = "system"  # Could be extracted from auth in a real implementation
            
            # Search for similar messages
            results = await embedding_service.search_similar_conversations(
                db=db,
                user_id=user_id,
                query_embedding=query_embedding,
                limit=request.limit
            )
            
            # Format the results
            formatted_results = []
            for result in results:
                # Get timestamp and handle it carefully
                timestamp = result.get("timestamp")
                formatted_timestamp = timestamp.isoformat() if timestamp else None
                
                formatted_results.append({
                    "content": result.get("content"),
                    "similarity": result.get("similarity_score"),
                    "timestamp": formatted_timestamp,
                    "conversation_id": result.get("conversation_id")
                })
            
            return {
                "results": formatted_results,
                "count": len(formatted_results)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error searching embeddings: {str(e)}")

# Create and export the router object with backward compatibility structure
router = EmbeddingRouter() 