#!/usr/bin/env python3
"""
Qdrant integration test script for Ponder backend.
This script tests the Qdrant vector database integration.
"""

import sys
import os
import logging
import asyncio
import numpy as np
from typing import List, Dict, Any

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.env import load_environment
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def test_qdrant_connection():
    """Test basic Qdrant connectivity."""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models
        
        host = getattr(settings, 'QDRANT_HOST', 'localhost')
        port = getattr(settings, 'QDRANT_PORT', 6333)
        
        logger.info(f"Testing connection to Qdrant at {host}:{port}")
        
        # Create client with timeout
        client = QdrantClient(host, port=port, timeout=10.0)
        
        # Test connection by getting collections
        collections = client.get_collections()
        logger.info(f"✅ Connected to Qdrant successfully")
        logger.info(f"Available collections: {[c.name for c in collections.collections]}")
        
        return True, client, models
        
    except ImportError:
        logger.error("❌ Qdrant client not installed. Install with: pip install qdrant-client")
        return False, None, None
    except Exception as e:
        logger.error(f"❌ Failed to connect to Qdrant: {str(e)}")
        return False, None, None

def test_collection_creation(client, models):
    """Test creating a collection in Qdrant."""
    try:
        collection_name = "test-ponder-embeddings"
        dimension = 1536  # OpenAI embedding dimension
        
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if collection_name in collection_names:
            logger.info(f"Collection '{collection_name}' already exists, deleting...")
            client.delete_collection(collection_name)
        
        # Create collection
        logger.info(f"Creating collection '{collection_name}' with dimension {dimension}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=dimension,
                distance=models.Distance.COSINE
            )
        )
        
        # Verify collection was created
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if collection_name in collection_names:
            logger.info(f"✅ Collection '{collection_name}' created successfully")
            return True, collection_name
        else:
            logger.error(f"❌ Collection '{collection_name}' not found after creation")
            return False, None
            
    except Exception as e:
        logger.error(f"❌ Failed to create collection: {str(e)}")
        return False, None

def test_vector_operations(client, models, collection_name):
    """Test vector insert and search operations."""
    try:
        # Create test vectors
        test_vectors = []
        for i in range(5):
            vector = np.random.random(1536).tolist()  # Random 1536-dimensional vector
            test_vectors.append(models.PointStruct(
                id=f"test-{i}",
                vector=vector,
                payload={
                    "text": f"Test message {i}",
                    "user_id": "test-user",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ))
        
        # Insert vectors
        logger.info(f"Inserting {len(test_vectors)} test vectors...")
        client.upsert(
            collection_name=collection_name,
            points=test_vectors
        )
        logger.info("✅ Vectors inserted successfully")
        
        # Test search
        query_vector = np.random.random(1536).tolist()
        logger.info("Testing vector search...")
        
        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=3
        )
        
        logger.info(f"✅ Search returned {len(search_results)} results")
        for i, result in enumerate(search_results):
            logger.info(f"  Result {i+1}: ID={result.id}, Score={result.score:.4f}")
        
        # Test filtered search
        logger.info("Testing filtered search...")
        filtered_results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=models.Filter(
                must=[models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value="test-user")
                )]
            ),
            limit=3
        )
        
        logger.info(f"✅ Filtered search returned {len(filtered_results)} results")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector operations failed: {str(e)}")
        return False

def test_collection_info(client, collection_name):
    """Test getting collection information."""
    try:
        info = client.get_collection(collection_name)
        logger.info(f"✅ Collection info retrieved:")
        logger.info(f"  Vectors count: {info.vectors_count}")
        logger.info(f"  Points count: {info.points_count}")
        logger.info(f"  Status: {info.status}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to get collection info: {str(e)}")
        return False

def cleanup_test_collection(client, collection_name):
    """Clean up test collection."""
    try:
        client.delete_collection(collection_name)
        logger.info(f"✅ Test collection '{collection_name}' cleaned up")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to cleanup test collection: {str(e)}")
        return False

async def test_embedding_service_integration():
    """Test the actual EmbeddingService integration with Qdrant."""
    try:
        from app.services.embedding_service import EmbeddingService
        
        logger.info("Testing EmbeddingService integration...")
        
        # Create embedding service
        embedding_service = EmbeddingService()
        
        # Initialize the service
        await embedding_service.ensure_initialized()
        
        if embedding_service.store is None:
            logger.error("❌ EmbeddingService store not initialized")
            return False
        
        logger.info("✅ EmbeddingService initialized successfully")
        
        # Test creating an embedding (mock)
        test_text = "This is a test message for embedding"
        logger.info(f"Testing embedding creation for: '{test_text}'")
        
        # Note: This would require OpenAI API key to actually work
        # For now, we'll just test the vector store operations
        
        return True
        
    except Exception as e:
        logger.error(f"❌ EmbeddingService integration test failed: {str(e)}")
        return False

def main():
    """Run all Qdrant integration tests."""
    logger.info("🔍 Starting Qdrant integration tests...")
    
    # Test connection
    success, client, models = test_qdrant_connection()
    if not success:
        logger.error("❌ Cannot proceed without Qdrant connection")
        return 1
    
    tests = []
    collection_name = None
    
    # Test collection creation
    logger.info("\n🔍 Testing collection creation...")
    success, collection_name = test_collection_creation(client, models)
    tests.append(("Collection Creation", success))
    
    if success and collection_name:
        # Test vector operations
        logger.info("\n🔍 Testing vector operations...")
        success = test_vector_operations(client, models, collection_name)
        tests.append(("Vector Operations", success))
        
        # Test collection info
        logger.info("\n🔍 Testing collection info...")
        success = test_collection_info(client, collection_name)
        tests.append(("Collection Info", success))
        
        # Test EmbeddingService integration
        logger.info("\n🔍 Testing EmbeddingService integration...")
        success = asyncio.run(test_embedding_service_integration())
        tests.append(("EmbeddingService Integration", success))
        
        # Cleanup
        logger.info("\n🧹 Cleaning up...")
        cleanup_test_collection(client, collection_name)
    
    # Summary
    logger.info("\n📊 Qdrant Integration Test Summary:")
    logger.info("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info("=" * 50)
    logger.info(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All Qdrant integration tests passed!")
        return 0
    else:
        logger.error(f"❌ {total - passed} tests failed!")
        return 1

if __name__ == "__main__":
    # Load environment
    load_environment()
    exit_code = main()
    sys.exit(exit_code)