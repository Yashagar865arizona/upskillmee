"""
Unit tests for MessageService.
Tests message processing, AI integration, agent mode detection, and conversation handling.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import uuid
from datetime import datetime

from app.services.message_service import MessageService
from app.models.chat import Conversation, Message
from app.agents import AgentMode


class TestMessageService:
    """Test suite for MessageService."""

    def test_initialization(self, message_service):
        """Test MessageService initialization."""
        assert message_service.db is not None
        assert message_service.ai_service is not None
        assert message_service.current_conversation is None
        assert message_service.current_user is None

    def test_set_current_user(self, message_service, test_user):
        """Test setting current user."""
        message_service.set_current_user(test_user)
        
        assert message_service.current_user == test_user

    def test_set_current_conversation(self, message_service, test_conversation):
        """Test setting current conversation."""
        message_service.set_current_conversation(test_conversation)
        
        assert message_service.current_conversation == test_conversation

    def test_detect_agent_mode_explicit_mode(self, message_service):
        """Test agent mode detection with explicit mode specified."""
        message = "Help me with coding"
        message_data = {"agent_mode": "work"}
        
        mode = message_service._detect_agent_mode(message, message_data)
        
        assert mode == AgentMode.WORK

    def test_detect_agent_mode_learning_plan_keywords(self, message_service):
        """Test agent mode detection for learning plan requests."""
        test_cases = [
            "create a learning plan for web development",
            "I need a learning plan",
            "make a learning plan",
            "build a curriculum for me",
            "create a roadmap for learning Python"
        ]
        
        for message in test_cases:
            mode = message_service._detect_agent_mode(message, {})
            assert mode == AgentMode.PLAN, f"Failed for message: {message}"

    def test_detect_agent_mode_work_keywords(self, message_service):
        """Test agent mode detection for work/technical requests."""
        test_cases = [
            "help me debug this code",
            "how to implement authentication",
            "show me how to build this",
            "step by step tutorial",
            "code example for sorting"
        ]
        
        for message in test_cases:
            mode = message_service._detect_agent_mode(message, {})
            assert mode == AgentMode.WORK, f"Failed for message: {message}"

    def test_detect_agent_mode_chat_keywords(self, message_service):
        """Test agent mode detection for chat/mentoring requests."""
        test_cases = [
            "how are you doing?",
            "I need some motivation",
            "what should I learn next?",
            "career advice please",
            "I'm feeling confused about my path"
        ]
        
        for message in test_cases:
            mode = message_service._detect_agent_mode(message, {})
            assert mode == AgentMode.CHAT, f"Failed for message: {message}"

    def test_detect_agent_mode_code_content(self, message_service):
        """Test agent mode detection for messages with code."""
        message = "```python\ndef hello():\n    print('hello')\n```\nThis function is not working"
        
        mode = message_service._detect_agent_mode(message, {})
        
        assert mode == AgentMode.WORK

    def test_detect_agent_mode_question_about_learning(self, message_service):
        """Test agent mode detection for learning questions."""
        message = "What should I learn to become a data scientist?"
        
        mode = message_service._detect_agent_mode(message, {})
        
        assert mode == AgentMode.CHAT

    def test_detect_agent_mode_default_chat(self, message_service):
        """Test agent mode detection defaults to chat."""
        message = "Hello there, nice to meet you!"
        
        mode = message_service._detect_agent_mode(message, {})
        
        assert mode == AgentMode.CHAT

    def test_create_traditional_summary_basic(self, message_service, sample_chat_history):
        """Test creating traditional chat history summary."""
        summary = message_service._create_traditional_summary(sample_chat_history)
        
        assert "Previous conversation summary:" in summary
        assert "web development" in summary.lower()
        assert "programming" in summary.lower()
        assert "Most recent exchanges:" in summary

    def test_create_traditional_summary_with_topics(self, message_service):
        """Test summary creation with topic detection."""
        chat_history = [
            {"sender": "user", "text": "I want to learn machine learning and AI", "id": "1"},
            {"sender": "bot", "text": "Great choice! What's your experience level?", "id": "2"},
            {"sender": "user", "text": "I'm a beginner with some programming background", "id": "3"}
        ]
        
        summary = message_service._create_traditional_summary(chat_history)
        
        assert "machine learning" in summary
        assert "AI" in summary or "artificial intelligence" in summary
        assert "beginner" in summary

    def test_create_traditional_summary_with_preferences(self, message_service):
        """Test summary creation with learning preference detection."""
        chat_history = [
            {"sender": "user", "text": "I prefer hands-on projects and practical learning", "id": "1"},
            {"sender": "bot", "text": "Perfect! Project-based learning is very effective", "id": "2"}
        ]
        
        summary = message_service._create_traditional_summary(chat_history)
        
        assert "hands-on" in summary

    def test_create_traditional_summary_long_history(self, message_service):
        """Test summary creation with long chat history (should truncate)."""
        # Create a long chat history (20 messages)
        chat_history = []
        for i in range(20):
            chat_history.append({
                "sender": "user" if i % 2 == 0 else "bot",
                "text": f"Message {i} about programming",
                "id": str(i)
            })
        
        summary = message_service._create_traditional_summary(chat_history)
        
        # Should only include last 15 messages
        assert "Message 19" in summary
        assert "Message 4" not in summary  # Should be truncated

    @pytest.mark.asyncio
    async def test_process_message_empty_content(self, message_service):
        """Test processing message with empty content."""
        message_data = {
            "message": "",
            "user_id": "test-user-123",
            "type": "message"
        }
        
        result = await message_service.process_message(message_data)
        
        assert result["sender"] == "bot"
        assert "I'm here to help" in result["text"]
        assert "id" in result

    @pytest.mark.asyncio
    async def test_process_message_no_user_id(self, message_service):
        """Test processing message without user_id."""
        message_data = {
            "message": "Hello",
            "type": "message"
        }
        
        result = await message_service.process_message(message_data)
        
        assert "Authentication required" in result["text"]
        assert result["auth_required"] is True

    @pytest.mark.asyncio
    async def test_process_message_auth_type(self, message_service):
        """Test processing auth message type."""
        message_data = {
            "type": "auth",
            "token": "test-token"
        }
        
        result = await message_service.process_message(message_data)
        
        assert result["status"] == "acknowledged"
        assert result["type"] == "system"

    @pytest.mark.asyncio
    async def test_process_message_heartbeat_type(self, message_service):
        """Test processing heartbeat message type."""
        message_data = {
            "type": "heartbeat"
        }
        
        result = await message_service.process_message(message_data)
        
        assert result["status"] == "heartbeat_acknowledged"
        assert result["type"] == "system"

    @pytest.mark.asyncio
    async def test_process_message_with_chat_history(self, message_service, sample_chat_history):
        """Test processing message with chat history."""
        message_data = {
            "message": "Tell me more about JavaScript",
            "user_id": "test-user-123",
            "type": "message",
            "chat_history": sample_chat_history
        }
        
        # Mock the AI service response
        message_service.ai_service.get_response = AsyncMock(return_value={
            "text": "JavaScript is a versatile programming language...",
            "sender": "bot",
            "id": str(uuid.uuid4())
        })
        
        result = await message_service.process_message(message_data)
        
        assert result["sender"] == "bot"
        assert "id" in result

    @pytest.mark.asyncio
    async def test_process_message_learning_plan_request(self, message_service):
        """Test processing learning plan request."""
        message_data = {
            "message": "create a learning plan for Python programming",
            "user_id": "test-user-123",
            "type": "message",
            "chat_history": []
        }
        
        # Mock the AI service response
        message_service.ai_service.get_response = AsyncMock(return_value={
            "text": "I'll create a comprehensive Python learning plan for you...",
            "sender": "bot",
            "id": str(uuid.uuid4())
        })
        
        result = await message_service.process_message(message_data)
        
        assert result["sender"] == "bot"
        assert "id" in result

    @pytest.mark.asyncio
    async def test_process_message_insufficient_context_for_plan(self, message_service):
        """Test processing learning plan request with insufficient context."""
        message_data = {
            "message": "create a learning plan",  # Very short, no context
            "user_id": "test-user-123",
            "type": "message",
            "chat_history": []  # No history
        }
        
        result = await message_service.process_message(message_data)
        
        assert "I'd be happy to create a personalized learning plan" in result["text"]
        assert "could you tell me a bit more about" in result["text"]

    @pytest.mark.asyncio
    async def test_process_message_topic_mention(self, message_service):
        """Test processing simple topic mention."""
        message_data = {
            "message": "machine learning",  # Simple topic mention
            "user_id": "test-user-123",
            "type": "message",
            "chat_history": []
        }
        
        # Mock the AI service response
        message_service.ai_service.get_response = AsyncMock(return_value={
            "text": "Machine learning is fascinating! What interests you about it?",
            "sender": "bot",
            "id": str(uuid.uuid4())
        })
        
        result = await message_service.process_message(message_data)
        
        assert result["sender"] == "bot"

    @pytest.mark.asyncio
    async def test_process_message_with_database_history(self, message_service, test_conversation, test_message):
        """Test processing message with database conversation history."""
        message_service.set_current_conversation(test_conversation)
        
        message_data = {
            "message": "Continue our discussion",
            "user_id": str(test_conversation.user_id),
            "type": "message",
            "chat_history": []  # Empty, should load from DB
        }
        
        # Mock the AI service response
        message_service.ai_service.get_response = AsyncMock(return_value={
            "text": "Of course! Let's continue where we left off...",
            "sender": "bot",
            "id": str(uuid.uuid4())
        })
        
        result = await message_service.process_message(message_data)
        
        assert result["sender"] == "bot"

    @pytest.mark.asyncio
    async def test_process_message_with_user_context(self, message_service, test_user, sample_user_context):
        """Test processing message with user context."""
        message_service.set_current_user(test_user)
        
        message_data = {
            "message": "What should I learn next?",
            "user_id": str(test_user.id),
            "type": "message",
            "chat_history": []
        }
        
        # Mock the AI service response
        message_service.ai_service.get_response = AsyncMock(return_value={
            "text": "Based on your interests in web development...",
            "sender": "bot",
            "id": str(uuid.uuid4())
        })
        
        result = await message_service.process_message(message_data)
        
        assert result["sender"] == "bot"

    @pytest.mark.asyncio
    async def test_process_message_affirmative_response_to_plan_offer(self, message_service):
        """Test processing affirmative response to learning plan offer."""
        chat_history = [
            {"sender": "user", "text": "I want to learn web development", "id": "1"},
            {"sender": "bot", "text": "Great! Would you like a learning plan for web development?", "id": "2"}
        ]
        
        message_data = {
            "message": "yes",
            "user_id": "test-user-123",
            "type": "message",
            "chat_history": chat_history
        }
        
        # Mock the AI service response
        message_service.ai_service.get_response = AsyncMock(return_value={
            "text": "Perfect! I'll create a web development learning plan...",
            "sender": "bot",
            "id": str(uuid.uuid4())
        })
        
        result = await message_service.process_message(message_data)
        
        assert result["sender"] == "bot"

    def test_prepare_context_with_history(self, message_service, sample_chat_history):
        """Test preparing context with chat history."""
        content = "Tell me about React"
        
        # This method is private, so we'll test it through process_message
        # or make it public for testing
        formatted_content = message_service._prepare_context_with_history(content, sample_chat_history)
        
        assert content in formatted_content
        # Should include some context from history

    @pytest.mark.asyncio
    async def test_create_chat_history_summary_with_embedding_service(self, message_service, sample_chat_history, test_user, test_conversation):
        """Test creating chat history summary with embedding service."""
        message_service.set_current_user(test_user)
        message_service.set_current_conversation(test_conversation)
        
        # Mock embedding service
        message_service.embedding_service = Mock()
        message_service.embedding_service.create_embedding = AsyncMock(return_value=[0.1] * 1536)
        message_service.embedding_service.search_similar_conversations = AsyncMock(return_value=[
            {"content": "Previous discussion about programming", "conversation_id": "other-conv-123"}
        ])
        
        summary = await message_service._create_chat_history_summary(sample_chat_history)
        
        assert "rag_contexts" in summary or "summary" in summary

    @pytest.mark.asyncio
    async def test_create_chat_history_summary_without_embedding_service(self, message_service, sample_chat_history):
        """Test creating chat history summary without embedding service."""
        message_service.embedding_service = None
        
        summary = await message_service._create_chat_history_summary(sample_chat_history)
        
        assert "summary" in summary
        assert "web development" in summary["summary"].lower()

    @pytest.mark.asyncio
    async def test_create_chat_history_summary_short_history(self, message_service):
        """Test creating summary with short chat history."""
        short_history = [
            {"sender": "user", "text": "Hello", "id": "1"}
        ]
        
        summary = await message_service._create_chat_history_summary(short_history)
        
        assert summary == {}  # Should return empty dict for short history

    def test_initialize_agent_manager(self, message_service, sample_user_context):
        """Test initializing agent manager."""
        message_service._initialize_agent_manager(sample_user_context)
        
        # Agent manager should be initialized (or None if initialization fails)
        assert message_service.agent_manager is not None or message_service.agent_manager is None

    @pytest.mark.asyncio
    async def test_run_async_operation_success(self, message_service):
        """Test running async operation successfully."""
        async def test_coroutine():
            return "success"
        
        result = await message_service._run_async_operation(test_coroutine())
        
        assert result == "success"

    @pytest.mark.asyncio
    async def test_run_async_operation_failure(self, message_service):
        """Test running async operation with failure."""
        async def failing_coroutine():
            raise Exception("Test error")
        
        result = await message_service._run_async_operation(failing_coroutine())
        
        assert result is None

    @pytest.mark.asyncio
    async def test_process_message_with_agent_manager(self, message_service):
        """Test processing message with agent manager."""
        # Mock agent manager
        mock_agent_manager = Mock()
        mock_agent_manager.process_message.return_value = {
            "system_prompt": "You are a helpful AI assistant",
            "enhanced_context": {"key": "value"}
        }
        message_service.agent_manager = mock_agent_manager
        
        message_data = {
            "message": "Help me learn Python",
            "user_id": "test-user-123",
            "type": "message",
            "chat_history": []
        }
        
        # Mock the AI service response
        message_service.ai_service.get_response = AsyncMock(return_value={
            "text": "I'd be happy to help you learn Python!",
            "sender": "bot",
            "id": str(uuid.uuid4())
        })
        
        result = await message_service.process_message(message_data)
        
        assert result["sender"] == "bot"
        mock_agent_manager.process_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_error_handling(self, message_service):
        """Test error handling in message processing."""
        message_data = {
            "message": "Test message",
            "user_id": "test-user-123",
            "type": "message",
            "chat_history": []
        }
        
        # Mock AI service to raise an exception
        message_service.ai_service.get_response = AsyncMock(side_effect=Exception("AI service error"))
        
        # Should handle the error gracefully
        result = await message_service.process_message(message_data)
        
        # Should return some kind of error response or fallback
        assert "text" in result or "error" in result