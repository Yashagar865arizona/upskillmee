"""
Unit tests for database models.
Tests model creation, relationships, validation, and database operations.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserProfile
from app.models.chat import Conversation, Message
from app.models.learning_plan import LearningPlan
from app.models.memory import Memory
from app.models.token_blacklist import TokenBlacklist


def _make_user(session, email, username, **kw):
    """Helper to create a user with required fields."""
    user = User()
    setattr(user, 'email', email)
    setattr(user, 'username', username)
    setattr(user, 'password_hash', kw.pop('password_hash', 'hashed_password'))
    for k, v in kw.items():
        setattr(user, k, v)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestUserModel:
    """Test suite for User model."""

    def test_user_creation(self, test_db_session):
        """Test basic user creation."""
        user = _make_user(test_db_session, 'create@example.com', 'createuser', name='Test User')

        assert user.id is not None
        assert user.email == 'create@example.com'
        assert user.username == 'createuser'
        assert user.name == 'Test User'
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_email_uniqueness(self, test_db_session):
        """Test that user emails must be unique."""
        _make_user(test_db_session, 'unique@example.com', 'unique1')

        user2 = User()
        setattr(user2, 'email', 'unique@example.com')
        setattr(user2, 'username', 'unique2')
        setattr(user2, 'password_hash', 'hash2')
        test_db_session.add(user2)

        with pytest.raises(IntegrityError):
            test_db_session.commit()
        test_db_session.rollback()

    def test_user_default_values(self, test_db_session):
        """Test user model default values."""
        user = _make_user(test_db_session, 'defaults@example.com', 'defaultsuser')

        assert user.is_active is True
        assert user.is_admin is False
        assert user.verification_token is None
        assert user.reset_password_token is None
        assert user.last_login is None

    def test_user_optional_fields(self, test_db_session):
        """Test user model with optional fields."""
        user = _make_user(
            test_db_session,
            'optional@example.com',
            'optionaluser',
            name='Optional User',
            is_verified=True,
            verification_token='verify_token_123',
            reset_password_token='reset_token_456',
            last_login=datetime.now(timezone.utc),
        )

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


class TestConversationModel:
    """Test suite for Conversation model."""

    def test_conversation_creation(self, test_db_session, test_user):
        """Test basic conversation creation."""
        conversation = Conversation()
        setattr(conversation, 'user_id', test_user.id)
        setattr(conversation, 'title', 'Learning Python')

        test_db_session.add(conversation)
        test_db_session.commit()
        test_db_session.refresh(conversation)

        assert conversation.id is not None
        assert conversation.user_id == test_user.id
        assert conversation.title == 'Learning Python'
        assert conversation.created_at is not None

    def test_conversation_default_values(self, test_db_session, test_user):
        """Test conversation model default values."""
        conversation = Conversation()
        setattr(conversation, 'user_id', test_user.id)

        test_db_session.add(conversation)
        test_db_session.commit()
        test_db_session.refresh(conversation)

        assert conversation.status == 'active'
        assert conversation.title is None

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
        setattr(message, 'user_id', test_conversation.user_id)
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
            'confidence': 0.95,
            'processing_time': 1.2,
            'tokens_used': 150
        }

        message = Message()
        setattr(message, 'user_id', test_conversation.user_id)
        setattr(message, 'conversation_id', test_conversation.id)
        setattr(message, 'content', 'Great question! Let me help you with that.')
        setattr(message, 'role', 'assistant')
        setattr(message, 'message_metadata', metadata)

        test_db_session.add(message)
        test_db_session.commit()
        test_db_session.refresh(message)

        assert message.message_metadata == metadata
        assert message.message_metadata['confidence'] == 0.95

    def test_message_role_validation(self, test_db_session, test_conversation):
        """Test message role values."""
        user_message = Message()
        setattr(user_message, 'user_id', test_conversation.user_id)
        setattr(user_message, 'conversation_id', test_conversation.id)
        setattr(user_message, 'content', 'User message')
        setattr(user_message, 'role', 'user')

        test_db_session.add(user_message)
        test_db_session.commit()

        assistant_message = Message()
        setattr(assistant_message, 'user_id', test_conversation.user_id)
        setattr(assistant_message, 'conversation_id', test_conversation.id)
        setattr(assistant_message, 'content', 'Assistant message')
        setattr(assistant_message, 'role', 'assistant')

        test_db_session.add(assistant_message)
        test_db_session.commit()

        assert user_message.role == 'user'
        assert assistant_message.role == 'assistant'

    def test_message_conversation_relationship(self, test_db_session, test_message):
        """Test message relationship with conversation."""
        conversation = test_db_session.query(Conversation).filter(
            Conversation.id == test_message.conversation_id
        ).first()

        assert conversation is not None
        assert conversation.id == test_message.conversation_id


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

        test_db_session.add(learning_plan)
        test_db_session.commit()
        test_db_session.refresh(learning_plan)

        assert learning_plan.id is not None
        assert learning_plan.title == 'Web Development Fundamentals'
        assert learning_plan.content == plan_content

    def test_learning_plan_default_values(self, test_db_session, test_user):
        """Test learning plan default values."""
        learning_plan = LearningPlan()
        setattr(learning_plan, 'user_id', test_user.id)
        setattr(learning_plan, 'title', 'Minimal Plan')
        setattr(learning_plan, 'content', {})

        test_db_session.add(learning_plan)
        test_db_session.commit()
        test_db_session.refresh(learning_plan)

        assert learning_plan.description is None
        assert learning_plan.created_at is not None

    def test_learning_plan_complex_content(self, test_db_session, test_user):
        """Test learning plan with complex content structure."""
        complex_content = {
            'title': 'Full Stack Development',
            'modules': [
                {
                    'name': 'Frontend',
                    'projects': [
                        {
                            'title': 'React App',
                            'skills': ['React', 'JavaScript', 'CSS'],
                        }
                    ]
                }
            ],
            'prerequisites': ['Basic JavaScript', 'HTML/CSS'],
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

    def test_learning_plan_user_relationship(self, test_db_session, test_learning_plan):
        """Test learning plan relationship with user."""
        user = test_db_session.query(User).filter(User.id == test_learning_plan.user_id).first()

        assert user is not None
        assert user.id == test_learning_plan.user_id


class TestMemoryModel:
    """Test suite for Memory model."""

    def test_memory_creation(self, test_db_session):
        """Test basic memory creation."""
        memory = Memory(
            content='User wants to learn Python programming',
            memory_type='conversation',
            meta_data={'conversation_id': 'conv-123'},
            user_id='user-456',
        )

        test_db_session.add(memory)
        test_db_session.commit()
        test_db_session.refresh(memory)

        assert memory.id is not None
        assert memory.content == 'User wants to learn Python programming'
        assert memory.memory_type == 'conversation'
        assert memory.meta_data == {'conversation_id': 'conv-123'}
        assert memory.user_id == 'user-456'
        assert memory.created_at is not None

    def test_memory_with_embedding(self, test_db_session):
        """Test memory with embedding vector."""
        embedding = [0.1] * 1536

        memory = Memory(
            content='Memory with embedding',
            memory_type='learning',
            meta_data={},
            embedding=embedding,
        )

        test_db_session.add(memory)
        test_db_session.commit()
        test_db_session.refresh(memory)

        assert memory.embedding is not None
        assert len(memory.embedding) == 1536

    def test_memory_default_values(self, test_db_session):
        """Test memory model default values."""
        memory = Memory(
            content='Basic memory',
            memory_type='reflection',
            meta_data={},
        )

        test_db_session.add(memory)
        test_db_session.commit()
        test_db_session.refresh(memory)

        assert memory.user_id is None
        assert memory.embedding is None

    def test_memory_complex_metadata(self, test_db_session):
        """Test memory with complex metadata."""
        complex_metadata = {
            'conversation_id': 'conv-789',
            'topics': ['programming', 'web development'],
            'user_context': {
                'skill_level': 'beginner',
                'interests': ['frontend', 'backend']
            },
        }

        memory = Memory(
            content='Complex memory with rich metadata',
            memory_type='conversation',
            meta_data=complex_metadata,
        )

        test_db_session.add(memory)
        test_db_session.commit()
        test_db_session.refresh(memory)

        assert memory.meta_data['topics'] == ['programming', 'web development']
        assert memory.meta_data['user_context']['skill_level'] == 'beginner'


class TestTokenBlacklistModel:
    """Test suite for TokenBlacklist model."""

    def test_token_blacklist_creation(self, test_db_session):
        """Test basic token blacklist creation."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        blacklisted_token = TokenBlacklist(
            token_jti='jti-123-456',
            user_id='user-789',
            expires_at=expires_at,
        )

        test_db_session.add(blacklisted_token)
        test_db_session.commit()
        test_db_session.refresh(blacklisted_token)

        assert blacklisted_token.id is not None
        assert blacklisted_token.token_jti == 'jti-123-456'
        assert blacklisted_token.user_id == 'user-789'

    def test_token_blacklist_uniqueness(self, test_db_session):
        """Test that token JTI must be unique."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        token1 = TokenBlacklist(
            token_jti='unique-jti-123',
            user_id='user-1',
            expires_at=expires_at,
        )
        test_db_session.add(token1)
        test_db_session.commit()

        token2 = TokenBlacklist(
            token_jti='unique-jti-123',
            user_id='user-2',
            expires_at=expires_at,
        )
        test_db_session.add(token2)

        with pytest.raises(IntegrityError):
            test_db_session.commit()
        test_db_session.rollback()


class TestModelRelationships:
    """Test suite for model relationships and constraints."""

    def test_user_profile_cascade_delete(self, test_db_session, test_user, test_user_profile):
        """Test that user profile is deleted when user is deleted."""
        user_id = test_user.id

        test_db_session.delete(test_user)
        test_db_session.commit()

        profile = test_db_session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        # With cascade="all, delete-orphan", profile should be deleted
        assert profile is None

    def test_conversation_messages_relationship(self, test_db_session, test_conversation):
        """Test relationship between conversation and messages."""
        message1 = Message()
        setattr(message1, 'user_id', test_conversation.user_id)
        setattr(message1, 'conversation_id', test_conversation.id)
        setattr(message1, 'content', 'First message')
        setattr(message1, 'role', 'user')

        message2 = Message()
        setattr(message2, 'user_id', test_conversation.user_id)
        setattr(message2, 'conversation_id', test_conversation.id)
        setattr(message2, 'content', 'Second message')
        setattr(message2, 'role', 'assistant')

        test_db_session.add_all([message1, message2])
        test_db_session.commit()

        messages = test_db_session.query(Message).filter(
            Message.conversation_id == test_conversation.id
        ).all()

        # May include the fixture message + 2 new ones
        assert len(messages) >= 2

    def test_user_multiple_learning_plans(self, test_db_session, test_user):
        """Test that a user can have multiple learning plans."""
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

        plans = test_db_session.query(LearningPlan).filter(
            LearningPlan.user_id == test_user.id
        ).all()

        assert len(plans) >= 2
        plan_titles = [plan.title for plan in plans]
        assert 'Python Basics' in plan_titles
        assert 'Web Development' in plan_titles
