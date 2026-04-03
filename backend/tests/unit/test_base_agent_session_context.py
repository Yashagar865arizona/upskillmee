"""
Unit tests for BaseAgent.get_session_continuity_context() and ChatAgent session opening.
"""

import pytest
from app.agents.chat_agent import ChatAgent


class TestBaseAgentSessionContext:
    def test_no_prior_context_returns_empty(self):
        agent = ChatAgent(user_context={"name": "Test"})
        result = agent.get_session_continuity_context()
        assert result == ""

    def test_first_time_user_returns_empty(self):
        agent = ChatAgent(user_context={
            "name": "Test",
            "prior_session_context": {"is_returning_user": False},
        })
        result = agent.get_session_continuity_context()
        assert result == ""

    def test_returning_user_includes_summary(self):
        agent = ChatAgent(user_context={
            "name": "Test",
            "prior_session_context": {
                "is_returning_user": True,
                "prior_summary": "User discussed Python basics.",
                "last_session_topics": ["python"],
                "last_session_at": "2026-04-01T12:00:00+00:00",
            },
        })
        result = agent.get_session_continuity_context()
        assert "Python basics" in result
        assert "python" in result
        assert "2026-04-01" in result

    def test_get_base_context_includes_session_continuity(self):
        agent = ChatAgent(user_context={
            "name": "Alice",
            "skill_level": "intermediate",
            "prior_session_context": {
                "is_returning_user": True,
                "prior_summary": "User was learning React hooks.",
                "last_session_topics": ["web development"],
                "last_session_at": "2026-04-02T10:00:00+00:00",
            },
        })
        ctx = agent.get_base_context()
        assert "Alice" in ctx
        assert "React hooks" in ctx
        assert "web development" in ctx


class TestChatAgentSessionOpening:
    def test_new_user_no_session_instruction(self):
        agent = ChatAgent(user_context={"name": "New User"})
        prompt = agent.get_system_prompt()
        assert "SESSION CONTINUITY" not in prompt

    def test_returning_user_gets_session_instruction(self):
        agent = ChatAgent(user_context={
            "name": "Returning User",
            "prior_session_context": {
                "is_returning_user": True,
                "prior_summary": "User explored ML.",
                "last_session_topics": ["machine learning"],
                "last_session_at": "2026-04-02T10:00:00+00:00",
            },
        })
        prompt = agent.get_system_prompt()
        assert "SESSION CONTINUITY" in prompt
        assert "machine learning" in prompt
        assert "Welcome back" in prompt or "Hey again" in prompt
