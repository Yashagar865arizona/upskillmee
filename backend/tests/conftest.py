"""
Test configuration and fixtures for Ponder backend tests.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import tempfile
import os

# Import models and services
from app.database.base import Base
import app.models  # noqa: F401 — ensure all ORM tables are registered on Base
from app.models.user import User, UserProfile
from app.models.chat import Conversation, Message
from app.models.learning_plan import LearningPlan
from app.models.memory import Memory
from app.models.token_blacklist import TokenBlacklist
from app.services.auth_service import AuthService
from app.services.message_service import MessageService
from app.services.learning_service import LearningService
from app.services.ai_integration_service import AIIntegrationService
from app.services.memory_service import MemoryService
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db_engine():
    """Create a test database engine using SQLite in memory.

    PostgreSQL-specific column types (ARRAY, UUID) are replaced with
    compatible equivalents before the schema is created on SQLite.
    """
    from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
    from sqlalchemy import JSON, String as SAString

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    from sqlalchemy import ARRAY as SA_ARRAY

    # Patch ARRAY → JSON and UUID → String for all mapped columns so that
    # Base.metadata.create_all succeeds against SQLite.
    patched: list = []
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, (ARRAY, SA_ARRAY)):
                patched.append((col, col.type))
                col.type = JSON()
            elif isinstance(col.type, PG_UUID):
                patched.append((col, col.type))
                col.type = SAString(36)

    Base.metadata.create_all(bind=engine)

    yield engine

    # Restore PostgreSQL-specific types after the engine fixture is torn down.
    for col, original_type in patched:
        col.type = original_type


@pytest.fixture
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """Alias for test_db_session used by integration tests."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def test_user(test_db_session) -> User:
    """Create a test user."""
    user = User()
    setattr(user, 'id', 'test-user-id-123')
    setattr(user, 'email', 'test@example.com')
    setattr(user, 'username', 'testuser')
    setattr(user, 'name', 'Test User')
    setattr(user, 'password_hash', '$2b$12$test.hash.value')
    setattr(user, 'is_verified', True)
    setattr(user, 'verification_token', None)
    setattr(user, 'reset_password_token', None)
    
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def test_user_profile(test_db_session, test_user) -> UserProfile:
    """Create a test user profile."""
    profile = UserProfile()
    setattr(profile, 'user_id', test_user.id)
    setattr(profile, 'email', test_user.email)
    setattr(profile, 'name', test_user.name)
    setattr(profile, 'learning_style', 'hands-on')
    setattr(profile, 'career_goals', ['software development'])
    setattr(profile, 'skill_levels', {'programming': 'beginner'})
    setattr(profile, 'interests', ['web development', 'AI'])
    
    test_db_session.add(profile)
    test_db_session.commit()
    test_db_session.refresh(profile)
    return profile


@pytest.fixture
def test_conversation(test_db_session, test_user) -> Conversation:
    """Create a test conversation."""
    conversation = Conversation()
    setattr(conversation, 'id', 'test-conversation-id-123')
    setattr(conversation, 'user_id', test_user.id)
    setattr(conversation, 'title', 'Test Learning Topic')
    
    test_db_session.add(conversation)
    test_db_session.commit()
    test_db_session.refresh(conversation)
    return conversation


@pytest.fixture
def test_message(test_db_session, test_conversation) -> Message:
    """Create a test message."""
    message = Message()
    setattr(message, 'id', 'test-message-id-123')
    setattr(message, 'user_id', test_conversation.user_id)
    setattr(message, 'conversation_id', test_conversation.id)
    setattr(message, 'content', 'Hello, I want to learn web development')
    setattr(message, 'role', 'user')
    
    test_db_session.add(message)
    test_db_session.commit()
    test_db_session.refresh(message)
    return message


@pytest.fixture
def test_learning_plan(test_db_session, test_user) -> LearningPlan:
    """Create a test learning plan."""
    plan_content = {
        "title": "Web Development Fundamentals",
        "description": "Learn the basics of web development",
        "projects": [
            {
                "title": "Build a Personal Website",
                "description": "Create your first HTML/CSS website",
                "skills": ["HTML", "CSS"],
                "estimated_hours": 10
            }
        ],
        "total_estimated_hours": 40,
        "difficulty_level": "beginner"
    }
    
    learning_plan = LearningPlan()
    setattr(learning_plan, 'id', 'test-plan-id-123')
    setattr(learning_plan, 'user_id', test_user.id)
    setattr(learning_plan, 'title', 'Web Development Fundamentals')
    setattr(learning_plan, 'description', 'Learn the basics of web development')
    setattr(learning_plan, 'content', plan_content)
    setattr(learning_plan, 'difficulty_level', 'beginner')
    setattr(learning_plan, 'estimated_hours', 40)
    setattr(learning_plan, 'skills', ['HTML', 'CSS', 'JavaScript'])
    setattr(learning_plan, 'status', 'active')
    
    test_db_session.add(learning_plan)
    test_db_session.commit()
    test_db_session.refresh(learning_plan)
    return learning_plan


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "This is a test AI response."
    mock_response.usage = Mock()
    mock_response.usage.total_tokens = 50
    mock_response.usage.prompt_tokens = 30
    mock_response.usage.completion_tokens = 20
    
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_embedding_response():
    """Mock embedding response for testing."""
    return {
        'data': [{'embedding': [0.1] * 1536}],
        'usage': {'total_tokens': 10}
    }


@pytest.fixture
def auth_service(test_db_session) -> AuthService:
    """Create AuthService instance for testing."""
    return AuthService(db=test_db_session)


@pytest.fixture
def message_service(test_db_session) -> MessageService:
    """Create MessageService instance for testing."""
    service = MessageService(db=test_db_session)
    # Mock the AI service to avoid external API calls
    service.ai_service = Mock()
    service.embedding_service = Mock()
    return service


@pytest.fixture
def learning_service() -> LearningService:
    """Create LearningService instance for testing."""
    return LearningService()


@pytest.fixture
def memory_service(test_db_session) -> MemoryService:
    """Create MemoryService instance for testing."""
    service = MemoryService(db=test_db_session)
    # Mock external dependencies
    service.client = Mock()
    service.embedding_service = Mock()
    return service


@pytest.fixture
def ai_integration_service() -> AIIntegrationService:
    """Create AIIntegrationService instance for testing."""
    service = AIIntegrationService()
    # Mock OpenAI client to avoid external API calls
    service.openai_client = Mock()
    service.deepseek_client = Mock()
    return service


@pytest.fixture
def test_client():
    """Create a test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_chat_history():
    """Sample chat history for testing."""
    return [
        {"sender": "user", "text": "Hello, I want to learn programming", "id": "msg1"},
        {"sender": "bot", "text": "Great! What type of programming interests you?", "id": "msg2"},
        {"sender": "user", "text": "I'm interested in web development", "id": "msg3"},
        {"sender": "bot", "text": "Web development is exciting! Would you like a learning plan?", "id": "msg4"}
    ]


@pytest.fixture
def sample_user_context():
    """Sample user context for testing."""
    return {
        "user_context": {
            "name": "Test User",
            "interests": ["web development", "programming"],
            "career_path": "software developer",
            "skill_level": "beginner"
        }
    }


# Async fixtures for async testing
@pytest.fixture
async def async_test_db_session(test_db_engine) -> AsyncGenerator[Session, None]:
    """Create an async test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("JWT_SECRET", "test-secret-key-for-testing-only")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("ENVIRONMENT", "test")


@pytest.fixture(autouse=True)
def _clear_rate_limit_stores(monkeypatch):
    """Reset all in-memory rate-limit stores and disable middleware rate limiting in tests."""
    # Clear service-level per-email rate limiters
    from app.services.auth_service import (
        _password_reset_timestamps,
        _resend_verification_timestamps,
    )
    _password_reset_timestamps.clear()
    _resend_verification_timestamps.clear()

    # Disable the RateLimitMiddleware check for tests — it uses in-memory
    # storage without Redis, and the store persists across tests causing 429s.
    import asyncio
    from app.middleware.security_middleware import RateLimitMiddleware

    async def _always_allow(*args, **kwargs):
        return True

    monkeypatch.setattr(RateLimitMiddleware, "_check_rate_limit", _always_allow)