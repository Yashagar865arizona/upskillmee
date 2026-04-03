from fastapi import BackgroundTasks
from datetime import datetime, timezone, timedelta
import asyncio
from sqlalchemy.orm import Session
from ..models.chat import EmbeddingStore, Message
import time
import logging
from ..services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

async def optimize_embedding_index(embedding_service: EmbeddingService):
    """Periodically optimize the FAISS index for better search performance"""
    while True:
        try:
            await embedding_service.update_index()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error(f"Error optimizing embedding index: {e}")
            await asyncio.sleep(300)  # Retry after 5 minutes on error 

async def cleanup_old_embeddings(db: Session, embedding_service: EmbeddingService):
    while True:
        try:
            # Remove embeddings older than 30 days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            db.query(Message).filter(
                Message.created_at < cutoff_date,
                Message.message_metadata.has_key('embedding')  # Check metadata instead
            ).update({
                Message.message_metadata: Message.message_metadata - 'embedding'
            }, synchronize_session=False)
            db.commit()
            
            # Rebuild FAISS index
            await embedding_service.initialize_index(db)
            await asyncio.sleep(86400)  # Run daily
        except Exception as e:
            logger.error(f"Error cleaning up embeddings: {e}")
            await asyncio.sleep(3600)

async def cleanup_embedding_cache(embedding_service: EmbeddingService):
    """Periodically clean up the embedding cache"""
    while True:
        try:
            current_time = datetime.now(timezone.utc)
            keys_to_remove = []
            
            for key, (timestamp, _) in embedding_service.embedding_cache.items():
                if (current_time - timestamp).total_seconds() > 3600:  # 1 hour TTL
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del embedding_service.embedding_cache[key]
                
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Error cleaning up embedding cache: {e}")
            await asyncio.sleep(60)

async def collect_embedding_metrics(embedding_service: EmbeddingService):
    while True:
        try:
            # Update metrics
            embedding_metrics.update_index_size(len(embedding_service.stored_embeddings))
            
            # Clean up old cache entries
            current_time = time.time()
            for key, (timestamp, _) in list(embedding_service.embedding_cache.items()):
                if current_time - timestamp > 3600:  # 1 hour TTL
                    del embedding_service.embedding_cache[key]
                    
            await asyncio.sleep(60)  # Collect metrics every minute
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            await asyncio.sleep(30)