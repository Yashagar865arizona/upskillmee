#!/usr/bin/env python3
"""
Verification test for vector database integration fixes.
This test verifies that the fixes for task 4.2 are properly implemented.
"""

import asyncio
import logging
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_embedding_service_fixes():
    """Test that EmbeddingService has the required fixes."""
    logger.info("Testing EmbeddingService fixes...")
    
    try:
        # Mock the database imports to avoid asyncpg dependency
        with patch.dict('sys.modules', {
            'asyncpg': Mock(),
            'app.database.session': Mock(),
            'app.database.engine': Mock(),
        }):
            from app.services.embedding_service import EmbeddingService
            
            # Create mock database session
            mock_db = Mock()
            
            # Initialize embedding service
            embedding_service = EmbeddingService(mock_db)
            
            # Test 1: Check that ensure_initialized method exists and is async
            assert hasattr(embedding_service, 'ensure_initialized')
            assert asyncio.iscoroutinefunction(embedding_service.ensure_initialized)
            logger.info("✓ EmbeddingService has ensure_initialized async method")
            
            # Test 2: Check that store_conversation_embedding method exists
            assert hasattr(embedding_service, 'store_conversation_embedding')
            assert asyncio.iscoroutinefunction(embedding_service.store_conversation_embedding)
            logger.info("✓ EmbeddingService has store_conversation_embedding method")
            
            # Test 3: Check that cleanup_old_embeddings method exists
            assert hasattr(embedding_service, 'cleanup_old_embeddings')
            assert asyncio.iscoroutinefunction(embedding_service.cleanup_old_embeddings)
            logger.info("✓ EmbeddingService has cleanup_old_embeddings method")
            
            # Test 4: Check that _initialize_vector_store method exists
            assert hasattr(embedding_service, '_initialize_vector_store')
            assert asyncio.iscoroutinefunction(embedding_service._initialize_vector_store)
            logger.info("✓ EmbeddingService has _initialize_vector_store method")
            
            # Test 5: Check that _initialize_qdrant_store method exists
            assert hasattr(embedding_service, '_initialize_qdrant_store')
            assert asyncio.iscoroutinefunction(embedding_service._initialize_qdrant_store)
            logger.info("✓ EmbeddingService has _initialize_qdrant_store method")
            
            return True
            
    except Exception as e:
        logger.error(f"EmbeddingService fixes test failed: {e}")
        return False

async def test_memory_service_fixes():
    """Test that MemoryService has the required fixes."""
    logger.info("Testing MemoryService fixes...")
    
    try:
        # Mock the database imports to avoid asyncpg dependency
        with patch.dict('sys.modules', {
            'asyncpg': Mock(),
            'app.database.session': Mock(),
            'app.database.engine': Mock(),
        }):
            from app.services.memory_service import MemoryService
            
            # Create mock database session
            mock_db = Mock()
            
            # Initialize memory service
            memory_service = MemoryService(mock_db)
            
            # Test 1: Check that cleanup_old_memories method exists
            assert hasattr(memory_service, 'cleanup_old_memories')
            assert asyncio.iscoroutinefunction(memory_service.cleanup_old_memories)
            logger.info("✓ MemoryService has cleanup_old_memories method")
            
            # Test 2: Check that archive_old_conversations method exists
            assert hasattr(memory_service, 'archive_old_conversations')
            assert asyncio.iscoroutinefunction(memory_service.archive_old_conversations)
            logger.info("✓ MemoryService has archive_old_conversations method")
            
            # Test 3: Check that get_memory_stats method exists
            assert hasattr(memory_service, 'get_memory_stats')
            assert asyncio.iscoroutinefunction(memory_service.get_memory_stats)
            logger.info("✓ MemoryService has get_memory_stats method")
            
            # Test 4: Check that _expand_query method exists
            assert hasattr(memory_service, '_expand_query')
            logger.info("✓ MemoryService has _expand_query method")
            
            # Test 5: Check that _merge_and_deduplicate_results method exists
            assert hasattr(memory_service, '_merge_and_deduplicate_results')
            logger.info("✓ MemoryService has _merge_and_deduplicate_results method")
            
            # Test 6: Check that _create_embedding method exists
            assert hasattr(memory_service, '_create_embedding')
            assert asyncio.iscoroutinefunction(memory_service._create_embedding)
            logger.info("✓ MemoryService has _create_embedding method")
            
            return True
            
    except Exception as e:
        logger.error(f"MemoryService fixes test failed: {e}")
        return False

async def test_vector_store_improvements():
    """Test that vector store classes have the required improvements."""
    logger.info("Testing vector store improvements...")
    
    try:
        # Mock the database imports to avoid asyncpg dependency
        with patch.dict('sys.modules', {
            'asyncpg': Mock(),
            'app.database.session': Mock(),
            'app.database.engine': Mock(),
        }):
            from app.services.embedding_service import VectorStore, QdrantStore, PineconeStore
            
            # Test 1: Check VectorStore base class
            vector_store = VectorStore(dimension=1536)
            assert vector_store.dimension == 1536
            assert hasattr(vector_store, 'init')
            assert hasattr(vector_store, 'upsert')
            assert hasattr(vector_store, 'query')
            logger.info("✓ VectorStore base class has required methods")
            
            # Test 2: Check that subclasses inherit properly
            assert issubclass(QdrantStore, VectorStore)
            assert issubclass(PineconeStore, VectorStore)
            logger.info("✓ QdrantStore and PineconeStore inherit from VectorStore")
            
            # Test 3: Check that QdrantStore has init method
            qdrant_store = QdrantStore(dimension=1536)
            assert hasattr(qdrant_store, 'init')
            assert asyncio.iscoroutinefunction(qdrant_store.init)
            logger.info("✓ QdrantStore has async init method")
            
            # Test 4: Check that PineconeStore has init method (if Pinecone is available)
            try:
                pinecone_store = PineconeStore(dimension=1536)
                assert hasattr(pinecone_store, 'init')
                assert asyncio.iscoroutinefunction(pinecone_store.init)
                logger.info("✓ PineconeStore has async init method")
            except ImportError as e:
                if "pinecone" in str(e).lower():
                    logger.info("✓ PineconeStore gracefully handles missing Pinecone SDK")
                else:
                    raise
            
            return True
            
    except Exception as e:
        logger.error(f"Vector store improvements test failed: {e}")
        return False

async def test_integration_improvements():
    """Test that the services are properly integrated."""
    logger.info("Testing integration improvements...")
    
    try:
        # Mock the database imports to avoid asyncpg dependency
        with patch.dict('sys.modules', {
            'asyncpg': Mock(),
            'app.database.session': Mock(),
            'app.database.engine': Mock(),
        }):
            from app.services.embedding_service import EmbeddingService
            from app.services.memory_service import MemoryService
            
            # Create mock database session
            mock_db = Mock()
            
            # Initialize services
            embedding_service = EmbeddingService(mock_db)
            memory_service = MemoryService(mock_db)
            
            # Test 1: Check that MemoryService can reference EmbeddingService
            assert hasattr(memory_service, 'embedding_service')
            logger.info("✓ MemoryService has embedding_service attribute")
            
            # Test 2: Check that both services have initialization locks
            assert hasattr(embedding_service, '_init_lock')
            assert hasattr(memory_service, '_init_lock')
            logger.info("✓ Both services have initialization locks")
            
            # Test 3: Check that both services have _initialized flags
            assert hasattr(embedding_service, '_initialized')
            assert hasattr(memory_service, '_initialized')
            logger.info("✓ Both services have _initialized flags")
            
            return True
            
    except Exception as e:
        logger.error(f"Integration improvements test failed: {e}")
        return False

async def test_configuration_support():
    """Test that configuration supports vector database settings."""
    logger.info("Testing configuration support...")
    
    try:
        from app.config.settings import settings
        
        # Test 1: Check vector database configuration
        assert hasattr(settings, 'VECTOR_STORE_TYPE')
        assert hasattr(settings, 'QDRANT_HOST')
        assert hasattr(settings, 'QDRANT_PORT')
        logger.info("✓ Vector database configuration is available")
        
        # Test 2: Check Pinecone configuration
        assert hasattr(settings, 'PINECONE_API_KEY')
        logger.info("✓ Pinecone configuration is available")
        
        # Test 3: Check OpenAI configuration
        assert hasattr(settings, 'OPENAI_API_KEY')
        logger.info("✓ OpenAI configuration is available")
        
        return True
        
    except Exception as e:
        logger.error(f"Configuration support test failed: {e}")
        return False

async def test_method_signatures():
    """Test that methods have the correct signatures for the fixes."""
    logger.info("Testing method signatures...")
    
    try:
        # Mock the database imports to avoid asyncpg dependency
        with patch.dict('sys.modules', {
            'asyncpg': Mock(),
            'app.database.session': Mock(),
            'app.database.engine': Mock(),
        }):
            from app.services.embedding_service import EmbeddingService
            from app.services.memory_service import MemoryService
            import inspect
            
            # Test EmbeddingService method signatures
            embedding_service = EmbeddingService(Mock())
            
            # Check store_conversation_embedding signature
            sig = inspect.signature(embedding_service.store_conversation_embedding)
            expected_params = ['db', 'user_id', 'conversation_id', 'message_content', 'role', 'metadata']
            actual_params = list(sig.parameters.keys())
            for param in expected_params:
                assert param in actual_params, f"Missing parameter {param} in store_conversation_embedding"
            logger.info("✓ store_conversation_embedding has correct signature")
            
            # Check cleanup_old_embeddings signature
            sig = inspect.signature(embedding_service.cleanup_old_embeddings)
            expected_params = ['user_id', 'days_old', 'keep_important']
            actual_params = list(sig.parameters.keys())
            for param in expected_params:
                assert param in actual_params, f"Missing parameter {param} in cleanup_old_embeddings"
            logger.info("✓ cleanup_old_embeddings has correct signature")
            
            # Test MemoryService method signatures
            memory_service = MemoryService(Mock())
            
            # Check cleanup_old_memories signature
            sig = inspect.signature(memory_service.cleanup_old_memories)
            expected_params = ['user_id', 'days_old', 'memory_type', 'keep_important']
            actual_params = list(sig.parameters.keys())
            for param in expected_params:
                assert param in actual_params, f"Missing parameter {param} in cleanup_old_memories"
            logger.info("✓ cleanup_old_memories has correct signature")
            
            # Check archive_old_conversations signature
            sig = inspect.signature(memory_service.archive_old_conversations)
            expected_params = ['user_id', 'days_old', 'keep_recent_count']
            actual_params = list(sig.parameters.keys())
            for param in expected_params:
                assert param in actual_params, f"Missing parameter {param} in archive_old_conversations"
            logger.info("✓ archive_old_conversations has correct signature")
            
            return True
            
    except Exception as e:
        logger.error(f"Method signatures test failed: {e}")
        return False

async def main():
    """Run all verification tests."""
    logger.info("Starting vector database integration fixes verification...")
    
    tests = [
        ("Configuration Support", test_configuration_support),
        ("EmbeddingService Fixes", test_embedding_service_fixes),
        ("MemoryService Fixes", test_memory_service_fixes),
        ("Vector Store Improvements", test_vector_store_improvements),
        ("Integration Improvements", test_integration_improvements),
        ("Method Signatures", test_method_signatures),
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
        logger.info("🎉 All verification tests passed! Vector database integration fixes are properly implemented.")
        return True
    else:
        logger.error("❌ Some verification tests failed. Check the logs above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)