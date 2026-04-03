"""
Test suite for memory router endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from app.main import app
from app.models.memory import MemoryType
import json

@pytest.fixture
def test_client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def mock_memory_service():
    """Create a mock memory service."""
    with patch("app.routers.memory_router.get_memory_service") as mock:
        service = Mock()
        mock.return_value = service
        yield service

def test_store_memory(test_client, mock_memory_service):
    """Test storing a memory through the API."""
    # Prepare test data
    memory_data = {
        "content": "Test memory content",
        "memory_type": MemoryType.CONVERSATION,
        "metadata": {"key": "value"},
        "user_id": "test_user"
    }

    # Mock service response
    mock_memory = Mock(
        id=1,
        content=memory_data["content"],
        memory_type=memory_data["memory_type"],
        metadata=memory_data["metadata"],
        user_id=memory_data["user_id"],
        created_at="2024-03-20T12:00:00"
    )
    mock_memory_service.store_memory = AsyncMock(return_value=mock_memory)

    # Make request
    response = test_client.post("/api/v1/memory/store", json=memory_data)

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["content"] == memory_data["content"]
    assert data["memory_type"] == memory_data["memory_type"]
    assert data["metadata"] == memory_data["metadata"]
    assert data["user_id"] == memory_data["user_id"]

def test_retrieve_memories(test_client, mock_memory_service):
    """Test retrieving memories through the API."""
    # Prepare test data
    query = "test query"
    memory_type = MemoryType.CONVERSATION
    user_id = "test_user"
    limit = 5

    # Mock service response
    mock_memories = [
        {
            "id": i,
            "content": f"Test memory {i}",
            "memory_type": memory_type,
            "metadata": {"key": f"value{i}"},
            "user_id": user_id,
            "similarity": 0.8,
            "created_at": "2024-03-20T12:00:00"
        } for i in range(3)
    ]
    mock_memory_service.retrieve_memories = AsyncMock(return_value=mock_memories)

    # Make request
    response = test_client.get(
        f"/api/v1/memory/retrieve?query={query}&memory_type={memory_type}&user_id={user_id}&limit={limit}"
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(isinstance(item, dict) for item in data)
    assert all("similarity" in item for item in data)

def test_perform_reasoning(test_client, mock_memory_service):
    """Test performing reasoning through the API."""
    # Prepare test data
    request_data = {
        "task": "Solve the equation: 2x + 5 = 15",
        "context": {"subject": "math", "difficulty": "easy"}
    }

    # Mock service response
    mock_result = {
        "steps": [
            {
                "reasoning": "First, I need to isolate x",
                "work": "2x + 5 = 15\n2x = 10\nx = 5",
                "verification": "2(5) + 5 = 15 ✓"
            }
        ],
        "duration": 1.5
    }
    mock_memory_service.self_play_reasoning = AsyncMock(return_value=mock_result)

    # Make request
    response = test_client.post("/api/v1/memory/reason", json=request_data)

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "steps" in data
    assert "duration" in data
    assert len(data["steps"]) == 1
    assert data["steps"][0]["reasoning"] == mock_result["steps"][0]["reasoning"]

def test_get_memory_stats(test_client, mock_memory_service):
    """Test getting memory statistics through the API."""
    # Mock service response
    mock_stats = {
        "chat_messages": 10,
        "learning_plans": 5,
        "reasoning_steps": 3,
        "context_data": 2
    }
    mock_memory_service.get_memory_stats = AsyncMock(return_value=mock_stats)

    # Make request
    response = test_client.get("/api/v1/memory/stats")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data == mock_stats

def test_error_handling(test_client, mock_memory_service):
    """Test error handling in API endpoints."""
    # Test store_memory error
    mock_memory_service.store_memory = AsyncMock(return_value=None)
    response = test_client.post("/api/v1/memory/store", json={
        "content": "test",
        "memory_type": MemoryType.CONVERSATION
    })
    assert response.status_code == 500
    assert "Failed to store memory" in response.json()["detail"]

    # Test retrieve_memories error
    mock_memory_service.retrieve_memories = AsyncMock(side_effect=Exception("Test error"))
    response = test_client.get("/api/v1/memory/retrieve?query=test")
    assert response.status_code == 500
    assert "Test error" in response.json()["detail"]

    # Test perform_reasoning error
    mock_memory_service.self_play_reasoning = AsyncMock(return_value={"error": "Test error"})
    response = test_client.post("/api/v1/memory/reason", json={"task": "test"})
    assert response.status_code == 500
    assert "Test error" in response.json()["detail"] 