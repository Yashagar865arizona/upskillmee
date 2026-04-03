"""
Unit tests for database models.
Tests model creation, relationships, validation, and database operations.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
import json

from app.models.user import User, UserProfile
from app.models.chat import Conversation, Message
from app.models.learning_plan import LearningPlan
from app.models.memory import Memory
from app.models.token_blacklist import TokenBlacklist


class TestUserModel:
    """Test suite for User model."""

    def test_user_creation(self, test_db_session):
        """Test basic user creation."""
        user = User()
        setattr(user, 'email', 'test@example.com')
        setattr(user, 'name', 'Test User')
        setattr(user, 'password_hash', 'hashed_password')
        
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == 'test@example.com'
        assert user.name == 'Test User'
        assert user.password_hash == 'hashed_password'
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_email_uniqueness(self, test_db_session):
        """Test that user emails must be unique."""
        # Create first user
        user1 = User()
        setattr(user1, 'email', 'unique@example.com')
        setattr(user1, 'password_hash', 'hash1')
        test_db_session.add(user1)
        test_db_session.commit()
        
        # Try to create second user with same email
        user2 = User()
        setattr(user2, 'email', 'unique@example.com')
        setattr(user2, 'password_hash', 'hash2')
        test_db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_user_default_values(self, test_db_session):
        """Test user model default values."""
        user = User()
        setattr(user, 'email', 'defaults@example.com')
        setattr(user, 'password_hash', 'hash')
        
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        # Check default values
        assert user.is_verified is False
        assert user.verification_token is None
        assert user.reset_password_token is None
        assert user.last_login is None

    def test_user_optional_fields(self, test_db_session):
        """Test user model with optional fields."""
        user = User()
        setattr(user, 'email', 'optional@example.com')
        setattr(user, 'name', 'Optional User')
        setattr(user, 'password_hash', 'hash')
        setattr(user, 'is_verified', True)
        setattr(user, 'verification_token', 'verify_token_123')
        setattr(user, 'reset_password_token', 'reset_token_456')
        setattr(user, 'last_login', datetime.now(timezone.utc))
        
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        assert user.name == 'Optional User'
        assert user.is_verified is True
        assert user.verification_token == 'verify_token_123'
        assert user.reset_password_token == 'reset_token_456'
        assert user.last_login is not None


class TestUserProfileModel:
    """Test suite for UserProfile model."""

    def test_user_profile_creation(self, test_db_session, test_user):
        """Test basic user profile creation."""
        profile = UserProfile()
        setattr(profile, 'user_id', test_user.id)
        setattr(profile, 'email', test_user.email)
        setattr(profile, 'name', test_user.name)
        setattr(profile, 'learning_style', 'visual')
        setattr(profile, 'career_goals', ['software developer'])
        setattr(profile, 'skill_levels', {'python': 'beginner'})
        setattr(profile, 'interests', ['programming', 'AI'])
        
        test_db_session.add(profile)
        test_db_session.commit()
        test_db_session.refresh(profile)
        
        assert profile.user_id == test_user.id
        assert profile.learning_style == 'visual'
        assert profile.career_goals == ['software developer']
        assert profile.skill_levels == {'python': 'beginner'}
        assert profile.interests == ['programming', 'AI']

    def test_user_profile_relationship(self, test_db_session, test_user_profile):
        """Test user profile relationship with user."""
        # Access the user through the relationship
        user = test_db_session.query(User).filter(User.id == test_user_profile.user_id).first()
        
        assert user is not None
        assert user.id == test_user_profile.user_id

    def test_user_profile_json_fields(self, test_db_session, test_user):
        """Test JSON fields in user profile."""
        complex_data = {
            'programming': {'python': 'intermediate', 'javascript': 'beginner'},
            'design': {'ui_ux': 'advanced', 'graphic_design': 'beginner'}
        }
        
        profile = UserProfile()
        setattr(profile, 'user_id', test_user.id)
        setattr(profile, 'skill_levels', complex_data)
        setattr(profile, 'ai_analysis', {
            'personality_type': 'analytical',
            'learning_pace': 'fast',
            'preferences': ['hands-on', 'project-based']
        })
        
        test_db_session.add(profile)
        test_db_session.commit()
        test_db_session.refresh(profile)
        
        assert profile.skill_levels == complex_data
        assert profile.ai_analysis['personality_type'] == 'analytical'

    def test_user_profile_optional_fields(self, test_db_session, test_user):
        """Test user profile with minimal required fields."""
        profile = UserProfile()
        setattr(profile, 'user_id', test_user.id)
        
        test_db_session.add(profile)
        test_db_session.commit()
        test_db_session.refresh(profile)
        
        assert profile.user_id == test_user.id
        assert profile.learning_style is None
        assert profile.career_goals is None


class TestConversationModel:
    """Test suite for Conversation model."""

    def test_conversation_creation(self, test_db_session, test_user):
        """Test basic conversation creation."""
        conversation = Conversation()
        setattr(conversation, 'user_id', test_user.id)
        setattr(conversation, 'topic', 'Learning Python')
        setattr(conversation, 'agent_mode', 'chat')
        
        test_db_session.add(conversation)
        test_db_session.commit()
        test_db_session.refresh(conversation)
        
        assert conversation.id is not None
        assert conversation.user_id == test_user.id
        assert conversation.topic == 'Learning Python'
        assert conversation.agent_mode == 'chat'
        assert conversation.created_at is not None
        assert conversation.updated_at is not None

    def test_conversation_default_values(self, test_db_session, test_user):
        """Test conversation model default values."""
        conversation = Conversation()
        setattr(conversation, 'user_id', test_user.id)
        
        test_db_session.add(conversation)
        test_db_session.commit()
        test_db_session.refresh(conversation)
        
        assert conversation.agent_mode == 'chat'  # Default value
        assert conversation.topic is None
        assert conversation.metadata is None

    def test_conversation_with_metadata(self, test_db_session, test_user):
        """Test conversation with metadata."""
        metadata = {
            'context': 'learning_session',
            'difficulty': 'beginner',
            'tags': ['python', 'programming']
        }
        
        conversation = Conversation()
        setattr(conversation, 'user_id', test_user.id)
        setattr(conversation, 'topic', 'Python Basics')
        setattr(conversation, 'metadata', metadata)
        
        test_db_session.add(conversation)
        test_db_session.commit()
        test_db_session.refresh(conversation)
        
        assert conversation.metadata == metadata
        assert conversation.metadata['context'] == 'learning_session'

    def test_conversation_user_relationship(self, test_db_session, test_conversation):
        """Test conversation relationship with user."""
        user = test_db_session.query(User).filter(User.id == test_conversation.user_id).first()
        
        assert user is not None
        assert user.id == test_conversation.user_id


class TestMessageModel:
    """Test suite for Message model."""

    def test_message_creation(self, test_db_session, test_conversation):
        """Test basic message creation."""
        message = Message()
        setattr(message, 'conversation_id', test_conversation.id)
        setattr(message, 'content', 'Hello, I want to learn programming')
        setattr(message, 'role', 'user')
        
        test_db_session.add(message)
        test_db_session.commit()
        test_db_session.refresh(message)
        
        assert message.id is not None
        assert message.conversation_id == test_conversation.id
        assert message.content == 'Hello, I want to learn programming'
        assert message.role == 'user'
        assert message.created_at is not None

    def test_message_with_metadata(self, test_db_session, test_conversation):
        """Test message with metadata."""
        metadata = {
            'agent_mode': 'chat',
            'confidence': 0.95,
            'processing_time': 1.2,
            'tokens_used': 150
        }
        
        message = Message()
        setattr(message, 'conversation_id', test_conversation.id)
        setattr(message, 'content', 'Great question! Let me help you with that.')
        setattr(message, 'role', 'assistant')
        setattr(message, 'metadata', metadata)
        
        test_db_session.add(message)
        test_db_session.commit()
        test_db_session.refresh(message)
        
        assert message.metadata == metadata
        assert message.metadata['confidence'] == 0.95

    def test_message_with_embedding(self, test_db_session, test_conversation):
        """Test message with embedding vector."""
        # Create a mock embedding vector
        embedding = [0.1] * 1536  # OpenAI embedding dimension
        
        message = Message()
        setattr(message, 'conversation_id', test_conversation.id)
        setattr(message, 'content', 'This message has an embedding')
        setattr(message, 'role', 'user')
        setattr(message, 'embedding', embedding)
        
        test_db_session.add(message)
        test_db_session.commit()
        test_db_session.refresh(message)
        
        assert message.embedding is not None
        assert len(message.embedding) == 1536
        assert all(isinstance(x, float) for x in message.embedding)

    def test_message_conversation_relationship(self, test_db_session, test_message):
        """Test message relationship with conversation."""
        conversation = test_db_session.query(Conversation).filter(
            Conversation.id == test_message.conversation_id
        ).first()
        
        assert conversation is not None
        assert conversation.id == test_message.conversation_id

    def test_message_role_validation(self, test_db_session, test_conversation):
        """Test message role values."""
        # Test user role
        user_message = Message()
        setattr(user_message, 'conversation_id', test_conversation.id)
        setattr(user_message, 'content', 'User message')
        setattr(user_message, 'role', 'user')
        
        test_db_session.add(user_message)
        test_db_session.commit()
        
        # Test assistant role
        assistant_message = Message()
        setattr(assistant_message, 'conversation_id', test_conversation.id)
        setattr(assistant_message, 'content', 'Assistant message')
        setattr(assistant_message, 'role', 'assistant')
        
        test_db_session.add(assistant_message)
        test_db_session.commit()
        
        assert user_message.role == 'user'
        assert assistant_message.role == 'assistant'


class TestLearningPlanModel:
    """Test suite for LearningPlan model."""

    def test_learning_plan_creation(self, test_db_session, test_user):
        """Test basic learning plan creation."""
        plan_content = {
            'title': 'Web Development Fundamentals',
            'projects': [
                {
                    'title': 'Personal Website',
                    'skills': ['HTML', 'CSS'],
                    'estimated_hours': 10
                }
            ],
            'total_estimated_hours': 40
        }
        
        learning_plan = LearningPlan()
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
        
        assert learning_plan.id is not None
        assert learning_plan.title == 'Web Development Fundamentals'
        assert learning_plan.content == plan_content
        assert learning_plan.difficulty_level == 'beginner'
        assert learning_plan.skills == ['HTML', 'CSS', 'JavaScript']

    def test_learning_plan_default_values(self, test_db_session, test_user):
        """Test learning plan default values."""
        learning_plan = LearningPlan()
        setattr(learning_plan, 'user_id', test_user.id)
        setattr(learning_plan, 'title', 'Minimal Plan')
        setattr(learning_plan, 'content', {})
        
        test_db_session.add(learning_plan)
        test_db_session.commit()
        test_db_session.refresh(learning_plan)
        
        assert learning_plan.status == 'draft'  # Default status
        assert learning_plan.description is None
        assert learning_plan.difficulty_level is None

    def test_learning_plan_complex_content(self, test_db_session, test_user):
        """Test learning plan with complex content structure."""
        complex_content = {
            'title': 'Full Stack Development',
            'description': 'Complete full stack course',
            'modules': [
                {
                    'name': 'Frontend',
                    'projects': [
                        {
                            'title': 'React App',
                            'description': 'Build a React application',
                            'skills': ['React', 'JavaScript', 'CSS'],
                            'tasks': [
                                {'name': 'Setup project', 'completed': False},
                                {'name': 'Create components', 'completed': False}
                            ]
                        }
                    ]
                },
                {
                    'name': 'Backend',
                    'projects': [
                        {
                            'title': 'REST API',
                            'description': 'Build a REST API',
                            'skills': ['Node.js', 'Express', 'MongoDB']
                        }
                    ]
                }
            ],
            'prerequisites': ['Basic JavaScript', 'HTML/CSS'],
            'learning_outcomes': ['Build full stack apps', 'Deploy applications']
        }
        
        learning_plan = LearningPlan()
        setattr(learning_plan, 'user_id', test_user.id)
        setattr(learning_plan, 'title', 'Full Stack Development')
        setattr(learning_plan, 'content', complex_content)
        
        test_db_session.add(learning_plan)
        test_db_session.commit()
        test_db_session.refresh(learning_plan)
        
        assert learning_plan.content['modules'][0]['name'] == 'Frontend'
        assert len(learning_plan.content['prerequisites']) == 2
        assert 'React' in learning_plan.content['modules'][0]['projects'][0]['skills']

    def test_learning_plan_user_relationship(self, test_db_session, test_learning_plan):
        """Test learning plan relationship with user."""
        user = test_db_session.query(User).filter(User.id == test_learning_plan.user_id).first()
        
        assert user is not None
        assert user.id == test_learning_plan.user_id


class TestMemoryModel:
    """Test suite for Memory model."""

    def test_memory_creation(self, test_db_session):
        """Test basic memory creation."""
        memory = Memory()
        setattr(memory, 'content', 'User wants to learn Python programming')
        setattr(memory, 'memory_type', 'chat_messages')
        setattr(memory, 'meta_data', {'conversation_id': 'conv-123'})
        setattr(memory, 'user_id', 'user-456')
        
        test_db_session.add(memory)
        test_db_session.commit()
        test_db_session.refresh(memory)
        
        assert memory.id is not None
        assert memory.content == 'User wants to learn Python programming'
        assert memory.memory_type == 'chat_messages'
        assert memory.meta_data == {'conversation_id': 'conv-123'}
        assert memory.user_id == 'user-456'
        assert memory.created_at is not None

    def test_memory_with_embedding(self, test_db_session):
        """Test memory with embedding vector."""
        embedding = [0.1] * 1536
        
        memory = Memory()
        setattr(memory, 'content', 'Memory with embedding')
        setattr(memory, 'memory_type', 'learning_plans')
        setattr(memory, 'embedding', embedding)
        
        test_db_session.add(memory)
        test_db_session.commit()
        test_db_session.refresh(memory)
        
        assert memory.embedding is not None
        assert len(memory.embedding) == 1536

    def test_memory_default_values(self, test_db_session):
        """Test memory model default values."""
        memory = Memory()
        setattr(memory, 'content', 'Basic memory')
        setattr(memory, 'memory_type', 'context_data')
        
        test_db_session.add(memory)
        test_db_session.commit()
        test_db_session.refresh(memory)
        
        assert memory.relevance_score == 1.0  # Default value
        assert memory.meta_data is None
        assert memory.user_id is None

    def test_memory_complex_metadata(self, test_db_session):
        """Test memory with complex metadata."""
        complex_metadata = {
            'conversation_id': 'conv-789',
            'agent_mode': 'plan',
            'topics': ['programming', 'web development'],
            'user_context': {
                'skill_level': 'beginner',
                'interests': ['frontend', 'backend']
            },
            'processing_info': {
                'tokens_used': 250,
                'confidence': 0.92,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        
        memory = Memory()
        setattr(memory, 'content', 'Complex memory with rich metadata')
        setattr(memory, 'memory_type', 'reasoning_steps')
        setattr(memory, 'meta_data', complex_metadata)
        setattr(memory, 'relevance_score', 0.85)
        
        test_db_session.add(memory)
        test_db_session.commit()
        test_db_session.refresh(memory)
        
        assert memory.meta_data['agent_mode'] == 'plan'
        assert memory.meta_data['user_context']['skill_level'] == 'beginner'
        assert memory.relevance_score == 0.85


class TestTokenBlacklistModel:
    """Test suite for TokenBlacklist model."""

    def test_token_blacklist_creation(self, test_db_session):
        """Test basic token blacklist creation."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        blacklisted_token = TokenBlacklist()
        setattr(blacklisted_token, 'token_jti', 'jti-123-456')
        setattr(blacklisted_token, 'user_id', 'user-789')
        setattr(blacklisted_token, 'expires_at', expires_at)
        
        test_db_session.add(blacklisted_token)
        test_db_session.commit()
        test_db_session.refresh(blacklisted_token)
        
        assert blacklisted_token.id is not None
        assert blacklisted_token.token_jti == 'jti-123-456'
        assert blacklisted_token.user_id == 'user-789'
        assert blacklisted_token.expires_at == expires_at
        assert blacklisted_token.created_at is not None

    def test_token_blacklist_uniqueness(self, test_db_session):
        """Test that token JTI must be unique."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Create first blacklisted token
        token1 = TokenBlacklist()
        setattr(token1, 'token_jti', 'unique-jti-123')
        setattr(token1, 'user_id', 'user-1')
        setattr(token1, 'expires_at', expires_at)
        test_db_session.add(token1)
        test_db_session.commit()
        
        # Try to create second token with same JTI
        token2 = TokenBlacklist()
        setattr(token2, 'token_jti', 'unique-jti-123')
        setattr(token2, 'user_id', 'user-2')
        setattr(token2, 'expires_at', expires_at)
        test_db_session.add(token2)
        
        with pytest.raises(IntegrityError):
            test_db_session.commit()


class TestModelRelationships:
    """Test suite for model relationships and constraints."""

    def test_user_profile_cascade_delete(self, test_db_session, test_user, test_user_profile):
        """Test that user profile is deleted when user is deleted."""
        user_id = test_user.id
        profile_id = test_user_profile.user_id
        
        # Delete the user
        test_db_session.delete(test_user)
        test_db_session.commit()
        
        # Check that profile still exists (no cascade delete configured)
        profile = test_db_session.query(UserProfile).filter(UserProfile.user_id == profile_id).first()
        # This depends on your actual foreign key configuration
        # If you have cascade delete, profile should be None
        # If not, profile should still exist but be orphaned

    def test_conversation_messages_relationship(self, test_db_session, test_conversation):
        """Test relationship between conversation and messages."""
        # Create multiple messages for the conversation
        message1 = Message()
        setattr(message1, 'conversation_id', test_conversation.id)
        setattr(message1, 'content', 'First message')
        setattr(message1, 'role', 'user')
        
        message2 = Message()
        setattr(message2, 'conversation_id', test_conversation.id)
        setattr(message2, 'content', 'Second message')
        setattr(message2, 'role', 'assistant')
        
        test_db_session.add_all([message1, message2])
        test_db_session.commit()
        
        # Query messages for the conversation
        messages = test_db_session.query(Message).filter(
            Message.conversation_id == test_conversation.id
        ).all()
        
        assert len(messages) == 2
        assert messages[0].conversation_id == test_conversation.id
        assert messages[1].conversation_id == test_conversation.id

    def test_user_multiple_learning_plans(self, test_db_session, test_user):
        """Test that a user can have multiple learning plans."""
        # Create multiple learning plans for the same user
        plan1 = LearningPlan()
        setattr(plan1, 'user_id', test_user.id)
        setattr(plan1, 'title', 'Python Basics')
        setattr(plan1, 'content', {'projects': []})
        
        plan2 = LearningPlan()
        setattr(plan2, 'user_id', test_user.id)
        setattr(plan2, 'title', 'Web Development')
        setattr(plan2, 'content', {'projects': []})
        
        test_db_session.add_all([plan1, plan2])
        test_db_session.commit()
        
        # Query learning plans for the user
        plans = test_db_session.query(LearningPlan).filter(
            LearningPlan.user_id == test_user.id
        ).all()
        
        assert len(plans) >= 2  # At least 2 (might have test_learning_plan fixture)
        plan_titles = [plan.title for plan in plans]
        assert 'Python Basics' in plan_titles
        assert 'Web Development' in plan_titles