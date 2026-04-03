#!/usr/bin/env python
"""
Test script for the embedding store functionality.
This script tests the connection to the embedding store and basic operations.
"""

import asyncio
import logging
import sys
from app.services.embedding_service import EmbeddingService
from app.config import settings
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("embedding-test")

async def test_embedding_store():
    """Test the embedding store functionality"""
    logger.info("Starting embedding store test")
    
    # Initialize the embedding service
    embedding_service = EmbeddingService()
    logger.info(f"Initialized embedding service with store type: {settings.VECTOR_STORE_TYPE}")
    
    # Test creating an embedding
    test_text = "This is a test message to verify the embedding store functionality"
    logger.info(f"Creating embedding for text: '{test_text}'")
    
    try:
        embedding = await embedding_service.create_embedding(test_text)
        if embedding is not None:
            logger.info(f"Successfully created embedding with shape: {embedding.shape}")
        else:
            logger.error("Failed to create embedding")
            return
    except Exception as e:
        logger.error(f"Error creating embedding: {e}")
        return
    
    # Test storing the embedding (without a database)
    if embedding_service.store:
        try:
            # Convert numpy array to list
            vector_list = embedding.tolist()
            if not isinstance(vector_list, list):
                vector_list = [float(x) for x in embedding.flatten()]
                
            # Store directly in vector store
            await embedding_service.store.upsert(
                vectors=[{
                    "id": "test-embedding-1",
                    "values": vector_list,
                    "metadata": {
                        "message_id": "test-message-1",
                        "text": test_text,
                        "timestamp": 1234567890
                    }
                }],
                namespace="test-user"
            )
            logger.info("Successfully stored test embedding in vector store")
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
    else:
        logger.error("Vector store not initialized, skipping storage test")
    
    # Test querying the embedding
    if embedding_service.store:
        try:
            # Query for similar vectors
            vector_list = embedding.tolist()
            if not isinstance(vector_list, list):
                vector_list = [float(x) for x in embedding.flatten()]
                
            results = await embedding_service.store.query(
                vector=vector_list,
                top_k=5,
                namespace="test-user"
            )
            
            if results and results.matches:
                logger.info(f"Successfully queried vector store, found {len(results.matches)} matches")
                for i, match in enumerate(results.matches):
                    logger.info(f"Match {i+1}: ID={match.id}, Score={match.score}, Metadata={match.metadata}")
            else:
                logger.warning("No matches found in vector store")
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
    else:
        logger.error("Vector store not initialized, skipping query test")
    
    logger.info("Embedding store test completed")

if __name__ == "__main__":
    asyncio.run(test_embedding_store())
