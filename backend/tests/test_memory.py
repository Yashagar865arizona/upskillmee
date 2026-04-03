"""
Refactored test suite for memory functionality.
Tests only the real, supported features of MemoryService and Memory model.
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from unittest.mock import AsyncMock, patch
import numpy as np
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.memory import Memory, MemoryType
from app.services.memory_service import MemoryService
from app.database import Base
from tenacity import RetryError

# Use the actual memory_type values from MemoryService.memory_types
MEMORY_TYPES = {
    "conversation": "chat_messages",
    "learning": "learning_plans",
    "reasoning": "reasoning_steps",
    "context": "context_data"
}

class TestMemory:
    """Test suite for memory functionality."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup_memory_service(self):
        """Set up test environment."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        self.db = Session()
        
        # Create memory service with mocked OpenAI client
        self.memory_service = MemoryService(self.db)
        
        # Mock the OpenAI client to avoid actual API calls
        mock_client = AsyncMock()
        mock_embeddings = AsyncMock()
        mock_chat = AsyncMock()
        
        # Setup mock response for embeddings
        mock_embeddings_response = AsyncMock()
        mock_embeddings_response.data = [AsyncMock(embedding=list(np.random.rand(1536)))]
        mock_embeddings.create.return_value = mock_embeddings_response
        
        # Setup mock response for chat completions
        mock_chat_response = AsyncMock()
        mock_chat_response.choices = [AsyncMock(message=AsyncMock(content=json.dumps([{"reasoning": "test", "work": "test", "verification": "test"}])))]
        mock_chat.completions.create.return_value = mock_chat_response
        
        # Assign mocks to client
        mock_client.embeddings = mock_embeddings
        mock_client.chat = mock_chat
        
        # Set mocked client
        self.memory_service.client = mock_client
        self.memory_service._initialized = True
        
        yield
        
        self.db.close()

    @pytest.mark.asyncio
    async def test_store_and_get_memory(self):
        """Test storing and retrieving a memory."""
        # Store a memory
        memory = await self.memory_service.store_memory(
            content="Test memory",
            memory_type=MEMORY_TYPES["conversation"],
            meta_data={"source": "test"}
        )
        
        assert memory is not None
        assert memory.content == "Test memory"
        assert memory.memory_type == MEMORY_TYPES["conversation"]
        assert memory.meta_data["source"] == "test"
        
        # Get the memory
        retrieved = await self.memory_service.get_memory(memory.id)
        assert retrieved is not None
        assert retrieved.id == memory.id
        assert retrieved.content == "Test memory"

    @pytest.mark.asyncio
    async def test_update_memory(self):
        """Test updating a memory."""
        # Create a memory
        memory = await self.memory_service.store_memory(
            content="Initial content",
            memory_type=MEMORY_TYPES["learning"],
            meta_data={"source": "test"}
        )
        
        # Update the memory
        updated = await self.memory_service.update_memory(
            memory_id=memory.id,
            content="Updated content",
            meta_data={"source": "test", "updated": True}
        )
        
        assert updated is not None
        assert updated.content == "Updated content"
        assert updated.meta_data["updated"] is True
        
        # Verify the update persisted
        retrieved = await self.memory_service.get_memory(memory.id)
        assert retrieved.content == "Updated content"
        assert retrieved.meta_data["updated"] is True

    @pytest.mark.asyncio
    async def test_delete_memory(self):
        """Test deleting a memory."""
        # Create a memory
        memory = await self.memory_service.store_memory(
            content="Delete me",
            memory_type=MEMORY_TYPES["reasoning"],
            meta_data={"source": "test"}
        )
        
        # Verify it exists
        assert await self.memory_service.get_memory(memory.id) is not None
        
        # Delete it
        result = await self.memory_service.delete_memory(memory.id)
        assert result is True
        
        # Verify it's gone
        assert await self.memory_service.get_memory(memory.id) is None

    @pytest.mark.asyncio
    async def test_list_memories(self):
        """Test listing memories."""
        # Create a few memories
        await self.memory_service.store_memory(
            content="List test 1",
            memory_type=MEMORY_TYPES["conversation"],
            meta_data={"source": "test", "list": True}
        )
        await self.memory_service.store_memory(
            content="List test 2",
            memory_type=MEMORY_TYPES["learning"],
            meta_data={"source": "test", "list": True}
        )
        
        # List all memories
        memories = await self.memory_service.list_memories()
        assert len(memories) >= 2
        
        # List memories of a specific type
        learning_memories = await self.memory_service.list_memories(memory_type=MEMORY_TYPES["learning"])
        assert len(learning_memories) >= 1
        assert all(m.memory_type == MEMORY_TYPES["learning"] for m in learning_memories)
        
        # List memories with specific metadata
        list_memories = await self.memory_service.list_memories(meta_data={"list": True})
        assert len(list_memories) >= 2

    @pytest.mark.asyncio
    async def test_search_memories(self):
        """Test searching memories."""
        # Create memories with searchable content
        await self.memory_service.store_memory(
            content="Python programming is fun",
            memory_type=MEMORY_TYPES["learning"],
            meta_data={"source": "test"}
        )
        await self.memory_service.store_memory(
            content="Learning about databases",
            memory_type=MEMORY_TYPES["learning"],
            meta_data={"source": "test"}
        )
        
        # Search for memories
        results = await self.memory_service.search_memories("Python", memory_type=MEMORY_TYPES["learning"])
        assert any("Python" in m.content for m in results)

    @pytest.mark.asyncio
    async def test_export_import_memories(self):
        memory = await self.memory_service.store_memory(
            content="Export me",
            memory_type=MEMORY_TYPES["reasoning"],
            meta_data={"source": "test"}
        )
        exported = await self.memory_service.export_memories([memory.id])
        assert len(exported) == 1
        imported = await self.memory_service.import_memories(exported)
        assert len(imported) == 1
        assert imported[0].content == "Export me"

    @pytest.mark.asyncio
    async def test_backup_and_restore(self):
        memory = await self.memory_service.store_memory(
            content="Backup this",
            memory_type=MEMORY_TYPES["context"],
            meta_data={"source": "test"}
        )
        backup = await self.memory_service.backup_memories()
        assert len(backup) >= 1
        
        # Clear memories by deleting
        await self.memory_service.delete_memory(memory.id)
        
        # Restore from backup
        restored = await self.memory_service.restore_memories(backup)
        assert len(restored) >= 1
        
        # Verify content is restored
        memories = await self.memory_service.list_memories()
        assert any(m.content == "Backup this" for m in memories)

    @pytest.mark.asyncio
    async def test_cleanup_memories(self):
        """Test cleaning up old memories."""
        # Create a memory that will be old
        memory = await self.memory_service.store_memory(
            content="Old memory",
            memory_type=MEMORY_TYPES["conversation"],
            meta_data={"source": "test"}
        )
        
        # Save the ID
        memory_id = memory.id
        
        # Set creation date to 31 days ago
        memory.created_at = datetime.now(timezone.utc) - timedelta(days=31)
        self.db.commit()
        
        # Create a new memory that should not be deleted
        new_memory = await self.memory_service.store_memory(
            content="New memory",
            memory_type=MEMORY_TYPES["conversation"],
            meta_data={"source": "test"}
        )
        
        # Cleanup memories older than 30 days
        result = await self.memory_service.cleanup_memories()
        assert result is True
        
        # Verify the old memory is gone by querying directly from the database
        old_memory_from_db = self.db.query(Memory).filter(Memory.id == memory_id).first()
        assert old_memory_from_db is None
        
        # Verify the new memory is still there
        new_memory_from_db = self.db.query(Memory).filter(Memory.id == new_memory.id).first()
        assert new_memory_from_db is not None

    @pytest.mark.asyncio
    async def test_get_memory_stats(self):
        await self.memory_service.store_memory(
            content="Stats test",
            memory_type=MEMORY_TYPES["conversation"],
            meta_data={"source": "test"}
        )
        
        stats = await self.memory_service.get_memory_stats()
        assert "total_memories" in stats
        assert stats["total_memories"] >= 1
        assert "memory_types" in stats
        assert MEMORY_TYPES["conversation"] in stats["memory_types"]

    @pytest.mark.asyncio
    async def test_memory_validation(self):
        """Test validation of memory inputs."""
        # Test empty content - expect RetryError instead of ValueError directly
        with pytest.raises(RetryError):
            await self.memory_service.store_memory(
                content="",
                memory_type=MEMORY_TYPES["conversation"],
                meta_data={"source": "test"}
            )
        
        # Test content too long
        with pytest.raises(RetryError):
            await self.memory_service.store_memory(
                content="x" * 10001,
                memory_type=MEMORY_TYPES["conversation"],
                meta_data={"source": "test"}
            )
        
        # Test invalid memory type
        with pytest.raises(RetryError):
            await self.memory_service.store_memory(
                content="Test content",
                memory_type="invalid_type",
                meta_data={"source": "test"}
            )
        
        # Test metadata too large
        large_metadata = {"data": "x" * 1000}
        with pytest.raises(RetryError):
            await self.memory_service.store_memory(
                content="Test content",
                memory_type=MEMORY_TYPES["conversation"],
                meta_data=large_metadata
            )

    @pytest.mark.asyncio
    async def test_memory_error_handling(self):
        """Test error handling for common failure scenarios."""
        # Test getting non-existent memory
        non_existent = await self.memory_service.get_memory("non_existent_id")
        assert non_existent is None
        
        # Test deleting non-existent memory
        result = await self.memory_service.delete_memory("non_existent_id")
        assert result is False
        
        # Test updating non-existent memory
        with pytest.raises(ValueError, match="Memory not found"):
            await self.memory_service.update_memory(
                "non_existent_id",
                content="Updated content"
            )

    @pytest.mark.asyncio
    async def test_memory_batch_operations(self):
        """Test batch operations on memories."""
        # Create batch of memories
        memories = []
        for i in range(5):
            memory = await self.memory_service.store_memory(
                content=f"Batch test {i}",
                memory_type=MEMORY_TYPES["conversation"],
                meta_data={"batch": True, "index": i}
            )
            memories.append(memory)
        
        # Test batch retrieval
        memory_ids = [m.id for m in memories]
        retrieved = await self.memory_service.get_memories(memory_ids)
        assert len(retrieved) == 5
        assert all(r.id in memory_ids for r in retrieved)
        
        # Test batch update
        updates = []
        for i, m in enumerate(memories):
            updates.append({
                "id": m.id,
                "content": f"Updated batch {i}",
                "meta_data": {"batch": True, "updated": True, "index": i}
            })
        
        updated = await self.memory_service.update_memories(updates)
        assert len(updated) == 5
        assert all("Updated batch" in m.content for m in updated)
        assert all(m.meta_data.get("updated") is True for m in updated)
        
        # Test batch deletion
        deleted = await self.memory_service.delete_memories(memory_ids)
        assert deleted is True
        
        # Verify all deleted
        remaining = await self.memory_service.get_memories(memory_ids)
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_memory_integration_with_reasoning(self):
        """Test the integration of memory with reasoning capabilities."""
        # Mock both the _generate_reasoning_steps and store_memory methods
        with patch.object(self.memory_service, '_generate_reasoning_steps') as mock_reason, \
             patch.object(self.memory_service, 'store_memory') as mock_store:
            
            # Setup mock response for reasoning steps
            mock_reason.return_value = [
                {"reasoning": "First, I need to understand what 2+2 means", 
                 "work": "2+2 is an addition operation", 
                 "verification": "This is correct"}
            ]
            
            # Setup mock response for store_memory
            mock_store.return_value = Memory(
                content=json.dumps(mock_reason.return_value),
                memory_type=MEMORY_TYPES["reasoning"],
                meta_data={"task": "Solve 2+2", "context": {"difficulty": "easy"}, "steps": 1}
            )
            
            # Test reasoning generation
            result = await self.memory_service.reason(
                task="Solve 2+2",
                context={"difficulty": "easy"}
            )
            
            # Verify result structure
            assert "steps" in result
            assert len(result["steps"]) > 0
            assert "duration" in result
            
            # Verify store_memory was called with correct parameters
            mock_store.assert_called_once()
            args, kwargs = mock_store.call_args
            assert kwargs["content"] == json.dumps(mock_reason.return_value)
            assert "meta_data" in kwargs
            assert kwargs["meta_data"]["task"] == "Solve 2+2"

class TestAgentMemory:
    """Test suite for agent memory integration."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup_agent(self):
        """Set up test environment."""
        # Create test database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        self.db = Session()
        
        self.memory_service = MemoryService(self.db)
        await self.memory_service.initialize()
        
        # Setup agent
        self.agent = Agent(memory_service=self.memory_service)
        await self.agent.initialize()
        
        yield
        
        # Cleanup
        await self.agent.close()
        self.db.close()
        
    @pytest.mark.asyncio
    async def test_agent_memory_recall(self):
        """Test that agent can recall memories."""
        # Store a test memory
        memory = await self.memory_service.store_memory(
            content="Python is a high-level programming language",
            memory_type=MEMORY_TYPES["learning"],
            meta_data={"source": "test"}
        )
        
        # Test agent memory recall
        memories = await self.agent.recall("Python programming")
        assert len(memories) > 0
        assert any("Python" in m["content"] for m in memories)
    
    # Define the Agent class for testing
class Agent:
    """Test agent class."""
    
    def __init__(self, memory_service):
        """Initialize agent."""
        self.memory_service = memory_service
    
    async def initialize(self):
        """Initialize agent."""
        pass
    
    async def recall(self, query, limit=5):
        """Recall memories related to query."""
        memories = await self.memory_service.search_memories(query, limit=limit)
        return [m.to_dict() for m in memories]
    
    async def close(self):
        """Close agent."""
        pass 

class TestMemoryWithChatIntegration:
    """Test integration between memory and chat functionality."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup_test_environment(self):
        """Set up test environment."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        self.db = Session()
        
        # Create memory service with mocked OpenAI client
        self.memory_service = MemoryService(self.db)
        
        # Mock the OpenAI client to avoid actual API calls
        mock_client = AsyncMock()
        mock_embeddings = AsyncMock()
        mock_chat = AsyncMock()
        
        # Setup mock response for embeddings
        mock_embeddings_response = AsyncMock()
        mock_embeddings_response.data = [AsyncMock(embedding=list(np.random.rand(1536)))]
        mock_embeddings.create.return_value = mock_embeddings_response
        
        # Setup mock response for chat completions
        mock_chat_response = AsyncMock()
        mock_chat_response.choices = [AsyncMock(message=AsyncMock(content=json.dumps([{"reasoning": "test", "work": "test", "verification": "test"}])))]
        mock_chat.completions.create.return_value = mock_chat_response
        
        # Assign mocks to client
        mock_client.embeddings = mock_embeddings
        mock_client.chat = mock_chat
        
        # Set mocked client
        self.memory_service.client = mock_client
        self.memory_service._initialized = True
        
        # Create test chat system
        self.chat_system = ChatSystem(self.memory_service)
        
        yield
        
        self.db.close()
        
    @pytest.mark.asyncio
    async def test_chat_memory_storage(self):
        """Test that chat messages are properly stored in memory."""
        # Send a message
        user_message = "Hello, I'm learning about Python programming."
        response = await self.chat_system.process_message(
            user_id="test_user",
            message=user_message
        )
        
        # Check memory was created
        memories = await self.memory_service.list_memories(
            memory_type=MEMORY_TYPES["conversation"]
        )
        assert len(memories) >= 1
        
        # Memory should contain the user message
        memory = memories[0]
        assert user_message in memory.content
        assert memory.meta_data.get("user_id") == "test_user"
        assert memory.meta_data.get("message_type") == "user"
        
        # Should also store assistant response
        memories = await self.memory_service.list_memories(
            memory_type=MEMORY_TYPES["conversation"],
            meta_data={"message_type": "assistant"}
        )
        assert len(memories) >= 1
        assistant_memory = memories[0]
        assert response in assistant_memory.content
    
    @pytest.mark.asyncio
    async def test_chat_history_retrieval(self):
        """Test retrieving chat history from memory."""
        # Create some chat history
        user_id = "history_test_user"
        messages = [
            "Hello, I'm a new user.",
            "I want to learn about machine learning.",
            "Can you tell me about neural networks?"
        ]
        
        # Send multiple messages
        for msg in messages:
            await self.chat_system.process_message(user_id=user_id, message=msg)
        
        # Retrieve chat history
        history = await self.chat_system.get_chat_history(user_id)
        
        # Should have all user messages and responses
        assert len(history) >= len(messages) * 2  # User + assistant for each
        
        # Messages should be in correct order
        user_messages = [m for m in history if m["role"] == "user"]
        for i, msg in enumerate(messages):
            assert user_messages[i]["content"] == msg
    
    @pytest.mark.asyncio
    async def test_contextual_memory_retrieval(self):
        """Test that memory is used for contextual understanding in chat."""
        # Create some background knowledge
        await self.memory_service.store_memory(
            content="Neural networks are a type of machine learning model inspired by the human brain.",
            memory_type=MEMORY_TYPES["learning"],
            meta_data={"topic": "machine_learning"}
        )
        
        # Ask a related question
        response = await self.chat_system.process_message(
            user_id="context_test_user",
            message="Tell me about neural networks"
        )
        
        # Check that relevant memories were retrieved during processing
        retrieved_memories = self.chat_system.last_retrieved_memories
        assert len(retrieved_memories) > 0
        assert any("neural networks" in m["content"].lower() for m in retrieved_memories)
        
        # The mock response won't actually use the memories, but we can verify the integration point

# Mock ChatSystem for testing integration
class ChatSystem:
    """Mock chat system for testing memory integration."""
    
    def __init__(self, memory_service):
        """Initialize chat system with memory service."""
        self.memory_service = memory_service
        self.last_retrieved_memories = []
    
    async def process_message(self, user_id: str, message: str) -> str:
        """Process a user message and store in memory."""
        # Store user message
        await self.memory_service.store_memory(
            content=message,
            memory_type=MEMORY_TYPES["conversation"],
            meta_data={"user_id": user_id, "message_type": "user", "timestamp": datetime.now(timezone.utc).isoformat()}
        )
        
        # Retrieve relevant memories for context
        self.last_retrieved_memories = await self.memory_service.retrieve_memories(
            query=message,
            limit=5
        )
        
        # Generate response (mocked)
        response = f"I've processed your message: '{message}'"
        
        # Store assistant response
        await self.memory_service.store_memory(
            content=response,
            memory_type=MEMORY_TYPES["conversation"],
            meta_data={"user_id": user_id, "message_type": "assistant", "timestamp": datetime.now(timezone.utc).isoformat()}
        )
        
        return response
    
    async def get_chat_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve chat history for a user."""
        # Get all conversation memories for this user
        memories = await self.memory_service.list_memories(
            memory_type=MEMORY_TYPES["conversation"],
            meta_data={"user_id": user_id}
        )
        
        # Format as chat history
        history = []
        for memory in sorted(memories, key=lambda m: m.meta_data.get("timestamp", "")):
            role = memory.meta_data.get("message_type", "user")
            history.append({
                "role": role,
                "content": memory.content,
                "timestamp": memory.meta_data.get("timestamp")
            })
        
        return history 