#!/usr/bin/env python3
"""
Simple test script to verify vector database integration fixes.
This tests the core functionality without requiring full database setup.
"""

import asyncio
import logging
import sys
import os
import numpy as np
from unittest.mock import Mock, AsyncMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_embedding_service_initialization():
    """Test that EmbeddingService can be initialized properly."""
    logger.info("Testing EmbeddingService initialization...")
    
    try:
        from app.services.embedding_service import EmbeddingService
        
        # Create mock database session
        mock_db = Mock()
        
        # Initialize embedding service
        embedding_service = EmbeddingService(mock_db)
        
        # Test that it has the expected attributes
        assert hasattr(embedding_service, 'dimension')
        assert embedding_service.dimension == 1536
        assert hasattr(embedding_service, '_initialized')
        assert hasattr(embedding_service, 'ensure_initialized')
        
        logger.info("✓ EmbeddingService has correct structure")
        
        # Test initialization method exists and is async
        assert asyncio.iscoroutinefunction(embedding_service.ensure_initialized)
        logger.info("✓ EmbeddingService.ensure_initialized is async")
        
        return True
        
    except Exception as e:
        logger.error(f"EmbeddingService initialization test failed: {e}")
        return False

async def test_memory_service_initialization():
    """Test that MemoryService can be initialized properly."""
    logger.info("Testing MemoryService initialization...")
    
    try:
        from app.services.memory_service import MemoryService
        
        # Create mock database session
        mock_db = Mock()
        
        # Initialize memory service
        memory_service = MemoryService(mock_db)
        
        # Test that it has the expected attributes
        assert hasattr(memory_service, 'db')
        assert hasattr(memory_service, '_initialized')
        assert hasattr(memory_service, 'initialize')
        assert hasattr(memory_service, 'memory_types')
        
        logger.info("✓ MemoryService has correct structure")
        
        # Test that memory types are defined
        expected_types = ["conversation", "learning", "reasoning", "context"]
        for memory_type in expected_types:
            assert memory_type in memory_service.memory_types
        
        logger.info("✓ MemoryService has correct memory types")
        
        # Test initialization method exists and is async
        assert asyncio.iscoroutinefunction(memory_service.initialize)
        logger.info("✓ MemoryService.initialize is async")
        
        return True
        
    except Exception as e:
        logger.error(f"MemoryService initialization test failed: {e}")
        return False

async def test_vector_store_classes():
    """Test that vector store classes are properly defined."""
    logger.info("Testing vector store classes...")
    
    try:
        from app.services.embedding_service import VectorStore, QdrantStore, PineconeStore
        
        # Test base VectorStore class
        vector_store = VectorStore(dimension=1536)
        assert vector_store.dimension == 1536
        assert hasattr(vector_store, 'init')
        assert hasattr(vector_store, 'upsert')
        assert hasattr(vector_store, 'query')
        
        logger.info("✓ VectorStore base class is properly defined")
        
        # Test that subclasses exist
        assert issubclass(QdrantStore, VectorStore)
        assert issubclass(PineconeStore, VectorStore)
        
        logger.info("✓ QdrantStore and PineconeStore inherit from VectorStore")
        
        return True
        
    except Exception as e:
        logger.error(f"Vector store classes test failed: {e}")
        return False

async def test_memory_service_methods():
    """Test that MemoryService has the required methods."""
    logger.info("Testing MemoryService methods...")
    
    try:
        from app.services.memory_service import MemoryService
        
        # Create mock database session
        mock_db = Mock()
        memory_service = MemoryService(mock_db)
        
        # Test that all required methods exist
        required_methods = [
            'store_memory',
            'get_memory',
            'search_memories',
            'cleanup_old_memories',
            'archive_old_conversations',
            'get_memory_stats'
        ]
        
        for method_name in required_methods:
            assert hasattr(memory_service, method_name)
            method = getattr(memory_service, method_name)
            assert asyncio.iscoroutinefunction(method)
        
        logger.info("✓ MemoryService has all required async methods")
        
        return True
        
    except Exception as e:
        logger.error(f"MemoryService methods test failed: {e}")
        return False

async def test_embedding_service_methods():
    """Test that EmbeddingService has the required methods."""
    logger.info("Testing EmbeddingService methods...")
    
    try:
        from app.services.embedding_service import EmbeddingService
        
        # Create mock database session
        mock_db = Mock()
        embedding_service = EmbeddingService(mock_db)
        
        # Test that all required methods exist
        required_methods = [
            'create_embedding',
            'store_conversation_embedding',
            'get_relevant_contexts',
            'cleanup_old_embeddings'
        ]
        
        for method_name in required_methods:
            assert hasattr(embedding_service, method_name)
            method = getattr(embedding_service, method_name)
            assert asyncio.iscoroutinefunction(method)
        
        logger.info("✓ EmbeddingService has all required async methods")
        
        return True
        
    except Exception as e:
        logger.error(f"EmbeddingService methods test failed: {e}")
        return False

async def test_configuration_loading():
    """Test that configuration is loaded properly."""
    logger.info("Testing configuration loading...")
    
    try:
        from app.config.settings import settings
        
        # Test that vector database settings exist
        assert hasattr(settings, 'VECTOR_STORE_TYPE')
        assert hasattr(settings, 'QDRANT_HOST')
        assert hasattr(settings, 'QDRANT_PORT')
        assert hasattr(settings, 'PINECONE_API_KEY')
        
        logger.info("✓ Vector database configuration settings are available")
        
        # Test that OpenAI settings exist
        assert hasattr(settings, 'OPENAI_API_KEY')
        
        logger.info("✓ OpenAI configuration settings are available")
        
        return True
        
    except Exception as e:
        logger.error(f"Configuration loading test failed: {e}")
        return False

async def test_imports():
    """Test that all required modules can be imported."""
    logger.info("Testing module imports...")
    
    try:
        # Test service imports
        from app.services.embedding_service import EmbeddingService
        from app.services.memory_service import MemoryService
        
        logger.info("✓ Service modules imported successfully")
        
        # Test model imports
        from app.models.memory import Memory
        
        logger.info("✓ Model modules imported successfully")
        
        # Test config imports
        from app.config.settings import settings
        
        logger.info("✓ Configuration modules imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Module imports test failed: {e}")
        return False

async def main():
    """Run all tests."""
    logger.info("Starting vector database integration tests (simple version)...")
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration Loading", test_configuration_loading),
        ("Vector Store Classes", test_vector_store_classes),
        ("EmbeddingService Initialization", test_embedding_service_initialization),
        ("MemoryService Initialization", test_memory_service_initialization),
        ("EmbeddingService Methods", test_embedding_service_methods),
        ("MemoryService Methods", test_memory_service_methods),
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
        logger.info("🎉 All tests passed! Vector database integration structure is correct.")
        return True
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)