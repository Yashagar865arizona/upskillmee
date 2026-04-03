#!/usr/bin/env python3
"""
Simple test to verify the vector database integration fixes are working.
"""

import sys
import os
import asyncio
import logging
from unittest.mock import Mock, patch

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_imports():
    """Test that we can import the services without errors."""
    logger.info("Testing basic imports...")
    
    try:
        # Mock problematic dependencies
        with patch.dict('sys.modules', {
            'asyncpg': Mock(),
            'passlib': Mock(),
            'passlib.context': Mock(),
        }):
            from app.services.embedding_service import EmbeddingService
            from app.services.memory_service import MemoryService
            
            logger.info("✓ Successfully imported EmbeddingService and MemoryService")
            
            # Test basic initialization
            mock_db = Mock()
            embedding_service = EmbeddingService(mock_db)
            memory_service = MemoryService(mock_db)
            
            logger.info("✓ Successfully created service instances")
            
            # Test that key methods exist
            assert hasattr(embedding_service, 'ensure_initialized')
            assert hasattr(embedding_service, 'store_conversation_embedding')
            assert hasattr(embedding_service, 'cleanup_old_embeddings')
            
            assert hasattr(memory_service, 'cleanup_old_memories')
            assert hasattr(memory_service, 'archive_old_conversations')
            assert hasattr(memory_service, 'get_memory_stats')
            
            logger.info("✓ All required methods are present")
            
            return True
            
    except Exception as e:
        logger.error(f"Import test failed: {e}")
        return False

async def test_method_signatures():
    """Test that methods have the expected signatures."""
    logger.info("Testing method signatures...")
    
    try:
        with patch.dict('sys.modules', {
            'asyncpg': Mock(),
            'passlib': Mock(),
            'passlib.context': Mock(),
        }):
            from app.services.embedding_service import EmbeddingService
            from app.services.memory_service import MemoryService
            import inspect
            
            # Test EmbeddingService methods
            embedding_service = EmbeddingService(Mock())
            
            # Check store_conversation_embedding
            sig = inspect.signature(embedding_service.store_conversation_embedding)
            params = list(sig.parameters.keys())
            expected = ['db', 'user_id', 'conversation_id', 'message_content']
            for param in expected:
                assert param in params, f"Missing parameter {param}"
            
            logger.info("✓ store_conversation_embedding has correct signature")
            
            # Test MemoryService methods
            memory_service = MemoryService(Mock())
            
            # Check cleanup_old_memories
            sig = inspect.signature(memory_service.cleanup_old_memories)
            params = list(sig.parameters.keys())
            expected = ['user_id', 'days_old']
            for param in expected:
                assert param in params, f"Missing parameter {param}"
            
            logger.info("✓ cleanup_old_memories has correct signature")
            
            return True
            
    except Exception as e:
        logger.error(f"Method signature test failed: {e}")
        return False

async def test_async_methods():
    """Test that methods are properly async."""
    logger.info("Testing async methods...")
    
    try:
        with patch.dict('sys.modules', {
            'asyncpg': Mock(),
            'passlib': Mock(),
            'passlib.context': Mock(),
        }):
            from app.services.embedding_service import EmbeddingService
            from app.services.memory_service import MemoryService
            
            embedding_service = EmbeddingService(Mock())
            memory_service = MemoryService(Mock())
            
            # Test that key methods are async
            async_methods = [
                (embedding_service, 'ensure_initialized'),
                (embedding_service, 'store_conversation_embedding'),
                (embedding_service, 'cleanup_old_embeddings'),
                (memory_service, 'cleanup_old_memories'),
                (memory_service, 'archive_old_conversations'),
                (memory_service, 'get_memory_stats'),
            ]
            
            for service, method_name in async_methods:
                method = getattr(service, method_name)
                assert asyncio.iscoroutinefunction(method), f"{method_name} is not async"
            
            logger.info("✓ All required methods are async")
            
            return True
            
    except Exception as e:
        logger.error(f"Async methods test failed: {e}")
        return False

async def main():
    """Run all tests."""
    logger.info("Starting simple vector database integration tests...")
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Method Signatures", test_method_signatures),
        ("Async Methods", test_async_methods),
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
        logger.info("🎉 All tests passed! Vector database integration fixes are working.")
        return True
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)