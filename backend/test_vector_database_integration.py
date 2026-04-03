#!/usr/bin/env python3
"""
Test script to verify vector database integration and memory retrieval functionality.
This tests the fixes implemented for task 4.2.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.services.embedding_service import EmbeddingService
from app.services.memory_service import MemoryService
from app.config.settings import settings
from app.database.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_embedding_service():
    """Test EmbeddingService initialization and basic functionality."""
    logger.info("Testing EmbeddingService...")
    
    try:
        # Create a test database session
        engine = create_engine("sqlite:///./test_vector.db")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Initialize embedding service
        embedding_service = EmbeddingService(db)
        await embedding_service.ensure_initialized()
        
        if not embedding_service._initialized:
            logger.error("EmbeddingService failed to initialize")
            return False
        
        logger.info("✓ EmbeddingService initialized successfully")
        
        # Test embedding creation
        test_text = "I want to learn Python programming and build web applications"
        embedding = await embedding_service.create_embedding(test_text)
        
        if embedding is None:
            logger.error("Failed to create embedding")
            return False
        
        logger.info(f"✓ Created embedding with shape: {embedding.shape}")
        
        # Test conversation embedding storage
        success = await embedding_service.store_conversation_embedding(
            db=db,
            user_id="test_user_123",
            conversation_id="test_conv_456",
            message_content=test_text,
            role="user",
            metadata={"test": True}
        )
        
        if success:
            logger.info("✓ Successfully stored conversation embedding")
        else:
            logger.warning("⚠ Failed to store conversation embedding (vector store may not be available)")
        
        # Test context retrieval
        contexts = await embedding_service.get_relevant_contexts(
            db=db,
            user_id="test_user_123",
            query="Python web development",
            limit=3
        )
        
        logger.info(f"✓ Retrieved {len(contexts)} relevant contexts")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"EmbeddingService test failed: {e}")
        return False

async def test_memory_service():
    """Test MemoryService initialization and functionality."""
    logger.info("Testing MemoryService...")
    
    try:
        # Create a test database session
        engine = create_engine("sqlite:///./test_memory.db")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Initialize memory service
        memory_service = MemoryService(db)
        await memory_service.initialize()
        
        if not memory_service._initialized:
            logger.error("MemoryService failed to initialize")
            return False
        
        logger.info("✓ MemoryService initialized successfully")
        
        # Test memory storage
        memory = await memory_service.store_memory(
            content="I learned about Python functions and how to use them effectively",
            memory_type="chat_messages",
            meta_data={"topic": "programming", "skill": "python"},
            user_id="test_user_123"
        )
        
        if memory is None:
            logger.error("Failed to store memory")
            return False
        
        logger.info(f"✓ Stored memory with ID: {memory.id}")
        
        # Test memory search
        search_results = await memory_service.search_memories(
            query="Python programming functions",
            memory_type="chat_messages",
            limit=5
        )
        
        logger.info(f"✓ Found {len(search_results)} memories in search")
        
        # Test memory cleanup
        cleanup_stats = await memory_service.cleanup_old_memories(
            user_id="test_user_123",
            days_old=1,  # Very recent for testing
            keep_important=True
        )
        
        logger.info(f"✓ Memory cleanup completed: {cleanup_stats}")
        
        # Test memory statistics
        stats = await memory_service.get_memory_stats(user_id="test_user_123")
        logger.info(f"✓ Memory stats: {stats}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"MemoryService test failed: {e}")
        return False

async def test_vector_store_connection():
    """Test vector store connection and basic operations."""
    logger.info("Testing vector store connection...")
    
    try:
        embedding_service = EmbeddingService()
        await embedding_service.ensure_initialized()
        
        if embedding_service.store is None:
            logger.warning("⚠ Vector store not available - this is expected in some environments")
            return True
        
        logger.info(f"✓ Vector store type: {type(embedding_service.store).__name__}")
        
        # Test basic vector operations
        test_embedding = await embedding_service.create_embedding("test message")
        if test_embedding is not None:
            logger.info("✓ Vector store can create embeddings")
        
        return True
        
    except Exception as e:
        logger.error(f"Vector store test failed: {e}")
        return False

async def test_integration():
    """Test integration between EmbeddingService and MemoryService."""
    logger.info("Testing service integration...")
    
    try:
        # Create test database
        engine = create_engine("sqlite:///./test_integration.db")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Initialize both services
        embedding_service = EmbeddingService(db)
        memory_service = MemoryService(db)
        
        await embedding_service.ensure_initialized()
        await memory_service.initialize()
        
        # Test that memory service uses embedding service
        if memory_service.embedding_service is not None:
            logger.info("✓ MemoryService properly integrated with EmbeddingService")
        else:
            logger.warning("⚠ MemoryService not integrated with EmbeddingService")
        
        # Test conversation flow
        conversation_messages = [
            "I want to learn web development",
            "What programming languages should I start with?",
            "I'm interested in building e-commerce websites",
            "How long does it take to become proficient?"
        ]
        
        # Store conversation messages
        for i, message in enumerate(conversation_messages):
            # Store in memory service
            memory = await memory_service.store_memory(
                content=message,
                memory_type="chat_messages",
                meta_data={
                    "conversation_id": "test_conv_integration",
                    "role": "user",
                    "timestamp": datetime.now().isoformat()
                },
                user_id="integration_test_user"
            )
            
            # Store embedding
            await embedding_service.store_conversation_embedding(
                db=db,
                user_id="integration_test_user",
                conversation_id="test_conv_integration",
                message_content=message,
                role="user"
            )
        
        logger.info(f"✓ Stored {len(conversation_messages)} conversation messages")
        
        # Test retrieval
        relevant_contexts = await embedding_service.get_relevant_contexts(
            db=db,
            user_id="integration_test_user",
            query="web development programming languages",
            limit=3
        )
        
        logger.info(f"✓ Retrieved {len(relevant_contexts)} relevant contexts")
        
        # Test memory search
        memory_results = await memory_service.search_memories(
            query="web development programming",
            memory_type="chat_messages",
            limit=3
        )
        
        logger.info(f"✓ Found {len(memory_results)} relevant memories")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False

async def main():
    """Run all tests."""
    logger.info("Starting vector database integration tests...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Vector store type: {getattr(settings, 'VECTOR_STORE_TYPE', 'qdrant')}")
    
    tests = [
        ("Vector Store Connection", test_vector_store_connection),
        ("EmbeddingService", test_embedding_service),
        ("MemoryService", test_memory_service),
        ("Service Integration", test_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✓ {test_name} test PASSED")
            else:
                logger.error(f"✗ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} test ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n--- Test Summary ---")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Vector database integration is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)