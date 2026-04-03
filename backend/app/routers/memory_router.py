"""
Router for memory operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..database import get_db
from ..services.memory_service import MemoryService
from ..models.memory import MemoryType
from pydantic import BaseModel

router = APIRouter(tags=["memory"])

class MemoryCreate(BaseModel):
    """Schema for creating a memory."""
    content: str
    memory_type: MemoryType
    meta_data: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "content": "Learned about Python functions.",
                "memory_type": "LEARNING",
                "meta_data": {"topic": "Python", "difficulty": "beginner"},
                "user_id": "user_123"
            }
        }

class MemoryResponse(BaseModel):
    """Schema for memory response."""
    id: int
    content: str
    memory_type: MemoryType
    meta_data: Optional[Dict[str, Any]]
    user_id: Optional[str]
    created_at: str
    similarity: Optional[float] = None

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "content": "Learned about Python functions.",
                "memory_type": "LEARNING",
                "meta_data": {"topic": "Python", "difficulty": "beginner"},
                "user_id": "user_123",
                "created_at": "2024-05-20T12:00:00",
                "similarity": 0.98
            }
        }

class ReasoningRequest(BaseModel):
    """Schema for reasoning request."""
    task: str
    context: Optional[Dict[str, Any]] = None

class ReasoningResponse(BaseModel):
    """Schema for reasoning response."""
    steps: List[Dict[str, Any]]
    duration: float

def get_memory_service(db: Session = Depends(get_db)) -> MemoryService:
    """Get memory service instance."""
    return MemoryService(db)

@router.post("/store", response_model=MemoryResponse)
async def store_memory(
    memory: MemoryCreate,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Store a new memory."""
    try:
        stored_memory = await memory_service.store_memory(
            content=memory.content,
            memory_type=memory.memory_type,
            meta_data=memory.meta_data,
            user_id=memory.user_id
        )
        if not stored_memory:
            raise HTTPException(status_code=500, detail="Failed to store memory")
        return stored_memory
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/retrieve", response_model=List[MemoryResponse])
async def retrieve_memories(
    query: str,
    memory_type: Optional[MemoryType] = None,
    user_id: Optional[str] = None,
    limit: int = 5,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Retrieve relevant memories."""
    try:
        memories = await memory_service.retrieve_memories(
            query=query,
            memory_type=memory_type,
            user_id=user_id,
            limit=limit
        )
        return [MemoryResponse(
            id=m["id"],
            content=m["content"],
            memory_type=m["memory_type"],
            meta_data=m.get("meta_data"),
            user_id=m.get("user_id"),
            created_at=m.get("created_at"),
            similarity=m.get("similarity")
        ) for m in memories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reason", response_model=ReasoningResponse)
async def perform_reasoning(
    request: ReasoningRequest,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Perform self-play reasoning."""
    try:
        result = await memory_service.self_play_reasoning(
            task=request.task,
            context=request.context
        )
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=Dict[str, int])
async def get_memory_stats(
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get memory statistics."""
    try:
        return await memory_service.get_memory_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 