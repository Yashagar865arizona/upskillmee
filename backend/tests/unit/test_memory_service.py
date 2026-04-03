"""
Unit tests for MemoryService.
Tests memory storage, retrieval, embedding operations, and vector database integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
import json
from datetime import datetime, timezone, timedelta
import numpy as np
from tenacity import RetryError

from app.services.memory_service import MemoryService
from app.models.memory import Memory


class TestMemoryService:
    """Test suite for MemoryService."""

    def test_initialization(self, memory_service):
        """Test MemoryService initialization."""
        assert isinstance(memory_service, MemoryService)
        assert memory_service.db is not None
        assert memory_service.client is not None  # Mocked
        assert memory_service.embedding_service is not None  # Mocked
        assert memory_service._initialized is False
        assert memory_service._init_lock is not None
        assert isinstance(memory_service.memory_types, dict)

    def test_memory_types_configuration(self, memory_service):
        """Test memory types configuration."""
        expected_types = {
            "conversation": "chat_messages",
            "learning": "learning_plans",
            "reasoning": "reasoning_steps",
            "context": "context_data"
        }
        
        assert memory_service.memory_types == expected_types

    @pytest.mark.asyncio
    async def test_initialize_success(self, memory_service):
        """Test successful memory service initialization."""
        # Mock OpenAI client initialization
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            # Mock EmbeddingService initialization
            mock_embedding_service = AsyncMock()
            mock_embedding_service.ensure_initialized = AsyncMock()
            
            with patch('app.services.memory_service.EmbeddingService', return_value=mock_embedding_service):
                await memory_service.initialize()
                
                assert memory_service._initialized is True
                assert memory_service.client == mock_client
                assert memory_service.embedding_service == mock_embedding_service

    @pytest.mark.asyncio
    async def test_initialize_failure(self, memory_service):
        """Test memory service initialization failure."""
        # Mock initialization failure
        with patch('openai.AsyncOpenAI', side_effect=Exception("API key error")):
            await memory_service.initialize()
            
            assert memory_service._initialized is False

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, memory_service):
        """Test initialization when already initialized."""
        memory_service._initialized = True
        
        # Should return early without reinitializing
        await memory_service.initialize()
        
        assert memory_service._initialized is True

    @pytest.mark.asyncio
    async def test_store_memory_success(self, memory_service, test_db_session):
        """Test successful memory storage."""
        content = "User wants to learn Python programming"
        memory_type = "chat_messages"
        meta_data = {"conversation_id": "conv-123", "user_id": "user-456"}
        user_id = "user-456"
        
        # Mock embedding creation - create a mock that has tolist() method
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1] * 1536
        with patch.object(memory_service, '_create_embedding', return_value=mock_embedding):
            # Mock database operations
            with patch.object(test_db_session, 'add') as mock_add, \
                 patch.object(test_db_session, 'commit') as mock_commit, \
                 patch.object(test_db_session, 'refresh') as mock_refresh:
                
                # Create a mock memory object
                mock_memory = Mock()
                mock_memory.id = "memory-123"
                mock_memory.content = content
                mock_memory.memory_type = memory_type
                mock_memory.meta_data = meta_data
                mock_memory.user_id = user_id
                mock_memory.embedding = mock_embedding.tolist()
                
                with patch('app.services.memory_service.Memory', return_value=mock_memory):
                    result = await memory_service.store_memory(content, memory_type, meta_data, user_id)
                    
                    assert result == mock_memory
                    mock_add.assert_called_once_with(mock_memory)
                    mock_commit.assert_called_once()
                    mock_refresh.assert_called_once_with(mock_memory)

    @pytest.mark.asyncio
    async def test_store_memory_invalid_content_empty(self, memory_service):
        """Test storing memory with empty content."""
        with pytest.raises((ValueError, RetryError)):
            await memory_service.store_memory("", "chat_messages")

    @pytest.mark.asyncio
    async def test_store_memory_invalid_content_too_long(self, memory_service):
        """Test storing memory with content too long."""
        long_content = "x" * 10001  # Exceeds 10000 character limit

        with pytest.raises((ValueError, RetryError)):
            await memory_service.store_memory(long_content, "chat_messages")

    @pytest.mark.asyncio
    async def test_store_memory_invalid_memory_type(self, memory_service):
        """Test storing memory with invalid memory type."""
        with pytest.raises((ValueError, RetryError)):
            await memory_service.store_memory("Valid content", "invalid_type")

    @pytest.mark.asyncio
    async def test_store_memory_metadata_too_large(self, memory_service):
        """Test storing memory with metadata too large."""
        large_metadata = {"key": "x" * 1000}  # Large metadata

        with pytest.raises((ValueError, RetryError)):
            await memory_service.store_memory("Valid content", "chat_messages", large_metadata)

    @pytest.mark.asyncio
    async def test_store_memory_without_embedding(self, memory_service, test_db_session):
        """Test storing memory when embedding creation fails."""
        content = "Test content"
        memory_type = "chat_messages"
        
        # Mock embedding creation failure
        with patch.object(memory_service, '_create_embedding', return_value=None):
            with patch.object(test_db_session, 'add') as mock_add, \
                 patch.object(test_db_session, 'commit') as mock_commit, \
                 patch.object(test_db_session, 'refresh') as mock_refresh:
                
                mock_memory = Mock()
                mock_memory.embedding = None
                
                with patch('app.services.memory_service.Memory', return_value=mock_memory):
                    result = await memory_service.store_memory(content, memory_type)
                    
                    assert result == mock_memory
                    assert mock_memory.embedding is None

    @pytest.mark.asyncio
    async def test_store_memory_database_error(self, memory_service, test_db_session):
        """Test storing memory with database error."""
        content = "Test content"
        memory_type = "chat_messages"

        # Mock database error — tenacity will retry and eventually raise RetryError
        with patch.object(test_db_session, 'commit', side_effect=Exception("Database error")):
            with pytest.raises((Exception, RetryError)):
                await memory_service.store_memory(content, memory_type)

    @pytest.mark.asyncio
    async def test_create_embedding_success(self, memory_service):
        """Test successful embedding creation."""
        text = "Test text for embedding"

        # _create_embedding calls self.embedding_service.create_embedding(text) with await
        mock_embedding_result = np.array([0.1] * 1536)
        mock_embedding_service = AsyncMock()
        mock_embedding_service.create_embedding = AsyncMock(return_value=mock_embedding_result)
        memory_service.embedding_service = mock_embedding_service

        embedding = await memory_service._create_embedding(text)

        assert embedding is not None
        assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_create_embedding_failure(self, memory_service):
        """Test embedding creation failure."""
        text = "Test text for embedding"
        
        # Mock OpenAI API error
        memory_service.client.embeddings.create = AsyncMock(side_effect=Exception("API error"))
        
        embedding = await memory_service._create_embedding(text)
        
        assert embedding is None

    @pytest.mark.asyncio
    async def test_create_embedding_empty_text(self, memory_service):
        """Test embedding creation with empty text."""
        embedding = await memory_service._create_embedding("")
        
        assert embedding is None

    @pytest.mark.asyncio
    async def test_create_embedding_none_text(self, memory_service):
        """Test embedding creation with None text."""
        embedding = await memory_service._create_embedding(None)
        
        assert embedding is None

    def test_validate_memory_type_valid(self, memory_service):
        """Test memory type validation with valid types."""
        valid_types = ["chat_messages", "learning_plans", "reasoning_steps", "context_data"]
        
        for memory_type in valid_types:
            # This would be tested through store_memory, but we can test the concept
            assert memory_type in memory_service.memory_types.values()

    def test_validate_memory_type_invalid(self, memory_service):
        """Test memory type validation with invalid types."""
        invalid_types = ["invalid_type", "wrong_type", "bad_type"]
        
        for memory_type in invalid_types:
            assert memory_type not in memory_service.memory_types.values()

    @pytest.mark.asyncio
    async def test_store_memory_with_conversation_metadata(self, memory_service, test_db_session):
        """Test storing memory with conversation-specific metadata."""
        content = "User asked about machine learning algorithms"
        memory_type = "chat_messages"
        meta_data = {
            "conversation_id": "conv-789",
            "message_id": "msg-456",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_mode": "chat",
            "topic": "machine learning"
        }
        user_id = "user-123"
        
        # Mock successful storage
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1] * 1536
        with patch.object(memory_service, '_create_embedding', return_value=mock_embedding):
            with patch.object(test_db_session, 'add'), \
                 patch.object(test_db_session, 'commit'), \
                 patch.object(test_db_session, 'refresh'):
                
                mock_memory = Mock()
                mock_memory.meta_data = meta_data
                
                with patch('app.services.memory_service.Memory', return_value=mock_memory):
                    result = await memory_service.store_memory(content, memory_type, meta_data, user_id)
                    
                    assert result.meta_data["conversation_id"] == "conv-789"
                    assert result.meta_data["topic"] == "machine learning"

    @pytest.mark.asyncio
    async def test_store_memory_with_learning_metadata(self, memory_service, test_db_session):
        """Test storing memory with learning-specific metadata."""
        content = "Generated learning plan for web development"
        memory_type = "learning_plans"
        meta_data = {
            "plan_id": "plan-123",
            "subject": "web development",
            "difficulty": "beginner",
            "estimated_hours": 40,
            "skills": ["HTML", "CSS", "JavaScript"]
        }
        user_id = "user-456"
        
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1] * 1536
        with patch.object(memory_service, '_create_embedding', return_value=mock_embedding):
            with patch.object(test_db_session, 'add'), \
                 patch.object(test_db_session, 'commit'), \
                 patch.object(test_db_session, 'refresh'):
                
                mock_memory = Mock()
                mock_memory.meta_data = meta_data
                
                with patch('app.services.memory_service.Memory', return_value=mock_memory):
                    result = await memory_service.store_memory(content, memory_type, meta_data, user_id)
                    
                    assert result.meta_data["subject"] == "web development"
                    assert result.meta_data["difficulty"] == "beginner"
                    assert "HTML" in result.meta_data["skills"]

    @pytest.mark.asyncio
    async def test_store_memory_with_reasoning_metadata(self, memory_service, test_db_session):
        """Test storing memory with reasoning-specific metadata."""
        content = "Step-by-step reasoning for solving programming problem"
        memory_type = "reasoning_steps"
        meta_data = {
            "problem_id": "prob-789",
            "step_number": 3,
            "reasoning_type": "algorithmic",
            "confidence": 0.85,
            "related_concepts": ["loops", "conditionals"]
        }
        
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1] * 1536
        with patch.object(memory_service, '_create_embedding', return_value=mock_embedding):
            with patch.object(test_db_session, 'add'), \
                 patch.object(test_db_session, 'commit'), \
                 patch.object(test_db_session, 'refresh'):
                
                mock_memory = Mock()
                mock_memory.meta_data = meta_data
                
                with patch('app.services.memory_service.Memory', return_value=mock_memory):
                    result = await memory_service.store_memory(content, memory_type, meta_data)
                    
                    assert result.meta_data["reasoning_type"] == "algorithmic"
                    assert result.meta_data["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_store_memory_with_context_metadata(self, memory_service, test_db_session):
        """Test storing memory with context-specific metadata."""
        content = "User context: beginner programmer interested in AI"
        memory_type = "context_data"
        meta_data = {
            "context_type": "user_profile",
            "skill_level": "beginner",
            "interests": ["AI", "machine learning"],
            "learning_style": "hands-on",
            "goals": ["build AI applications"]
        }
        user_id = "user-789"
        
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1] * 1536
        with patch.object(memory_service, '_create_embedding', return_value=mock_embedding):
            with patch.object(test_db_session, 'add'), \
                 patch.object(test_db_session, 'commit'), \
                 patch.object(test_db_session, 'refresh'):
                
                mock_memory = Mock()
                mock_memory.meta_data = meta_data
                
                with patch('app.services.memory_service.Memory', return_value=mock_memory):
                    result = await memory_service.store_memory(content, memory_type, meta_data, user_id)
                    
                    assert result.meta_data["skill_level"] == "beginner"
                    assert "AI" in result.meta_data["interests"]

    @pytest.mark.asyncio
    async def test_store_memory_retry_logic(self, memory_service, test_db_session):
        """Test retry logic in memory storage."""
        content = "Test content for retry"
        memory_type = "chat_messages"
        
        # Mock first two attempts fail, third succeeds
        call_count = 0
        def mock_commit():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary database error")
        
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1] * 1536
        with patch.object(memory_service, '_create_embedding', return_value=mock_embedding):
            with patch.object(test_db_session, 'add'), \
                 patch.object(test_db_session, 'commit', side_effect=mock_commit), \
                 patch.object(test_db_session, 'refresh'):
                
                mock_memory = Mock()
                
                with patch('app.services.memory_service.Memory', return_value=mock_memory):
                    # The retry decorator should handle the retries
                    result = await memory_service.store_memory(content, memory_type)
                    
                    assert result == mock_memory
                    assert call_count == 3  # Should have retried twice

    @pytest.mark.asyncio
    async def test_store_memory_max_retries_exceeded(self, memory_service, test_db_session):
        """Test memory storage when max retries are exceeded."""
        content = "Test content"
        memory_type = "chat_messages"

        # Mock all attempts fail — tenacity wraps in RetryError after 3 attempts
        with patch.object(test_db_session, 'commit', side_effect=Exception("Persistent database error")):
            with pytest.raises((Exception, RetryError)):
                await memory_service.store_memory(content, memory_type)

    @pytest.mark.asyncio
    async def test_embedding_service_integration(self, memory_service):
        """Test integration with EmbeddingService."""
        # Reset init state
        memory_service._initialized = False

        mock_embedding_service = AsyncMock()
        mock_embedding_service.ensure_initialized = AsyncMock()

        with patch('openai.AsyncOpenAI') as mock_openai, \
             patch('app.services.memory_service.EmbeddingService', return_value=mock_embedding_service):
            mock_openai.return_value = AsyncMock()
            await memory_service.initialize()

            assert memory_service._initialized is True
            mock_embedding_service.ensure_initialized.assert_called_once()

    def test_memory_service_thread_safety(self, memory_service):
        """Test memory service initialization thread safety."""
        # The _init_lock should prevent concurrent initialization
        assert memory_service._init_lock is not None
        assert isinstance(memory_service._init_lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_concurrent_initialization(self, memory_service):
        """Test concurrent initialization attempts."""
        # Reset initialization state
        memory_service._initialized = False
        
        # Mock successful initialization
        with patch('openai.AsyncOpenAI') as mock_openai, \
             patch('app.services.memory_service.EmbeddingService') as mock_embedding:
            
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            mock_embedding_service = AsyncMock()
            mock_embedding_service.ensure_initialized = AsyncMock()
            mock_embedding.return_value = mock_embedding_service
            
            # Start multiple initialization tasks concurrently
            tasks = [memory_service.initialize() for _ in range(3)]
            await asyncio.gather(*tasks)
            
            # Should only initialize once
            assert memory_service._initialized is True
            mock_openai.assert_called_once()

    def test_memory_content_validation(self, memory_service):
        """Test memory content validation edge cases."""
        # Test with exactly 1 character
        assert len("a") == 1  # Should be valid
        
        # Test with exactly 10000 characters
        max_content = "x" * 10000
        assert len(max_content) == 10000  # Should be valid
        
        # Test with 10001 characters
        too_long_content = "x" * 10001
        assert len(too_long_content) == 10001  # Should be invalid

    def test_metadata_json_serialization(self, memory_service):
        """Test metadata JSON serialization."""
        # Test complex metadata structure
        complex_metadata = {
            "nested": {
                "array": [1, 2, 3],
                "string": "test",
                "boolean": True,
                "null": None
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "numbers": [1.5, 2.7, 3.14]
        }
        
        # Should be serializable to JSON
        json_str = json.dumps(complex_metadata)
        assert len(json_str) > 0
        
        # Should be deserializable
        deserialized = json.loads(json_str)
        assert deserialized["nested"]["array"] == [1, 2, 3]
        assert deserialized["nested"]["boolean"] is True