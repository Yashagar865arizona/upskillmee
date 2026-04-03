"""
Session continuity service — loads prior conversation context so the AI Mentor can
resume naturally when a user returns.

Responsibilities:
- Load messages from previous sessions (not just the current conversation)
- Produce a compact prior-session summary for the system prompt
- Compress long in-session histories to stay within token limits
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models.chat import Conversation, Message

logger = logging.getLogger(__name__)

# Approximate characters per token (conservative estimate for GPT-4)
_CHARS_PER_TOKEN = 4
# Max tokens to spend on history before compressing
_MAX_HISTORY_TOKENS = 2000
_MAX_HISTORY_CHARS = _MAX_HISTORY_TOKENS * _CHARS_PER_TOKEN

# How many prior conversations to consider
_PRIOR_CONV_LIMIT = 3
# How many messages to pull from each prior conversation
_PRIOR_MSGS_PER_CONV = 20


class SessionContinuityService:
    """Provides cross-session memory for the AI Mentor."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_prior_session_context(
        self,
        user_id: str,
        current_conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return a structured dict describing the user's prior sessions.

        Keys:
            is_returning_user (bool)
            prior_summary (str)         — formatted for the system prompt
            last_session_topics (list)  — key topics from last session
            last_session_at (str|None)  — ISO timestamp of last activity
        """
        try:
            prior_convs = self._get_prior_conversations(user_id, current_conversation_id)
            if not prior_convs:
                return {"is_returning_user": False, "prior_summary": "", "last_session_topics": [], "last_session_at": None}

            all_messages: List[Message] = []
            for conv in prior_convs:
                msgs = (
                    self.db.query(Message)
                    .filter(Message.conversation_id == conv.id)
                    .order_by(Message.created_at.desc())
                    .limit(_PRIOR_MSGS_PER_CONV)
                    .all()
                )
                all_messages.extend(reversed(msgs))

            if not all_messages:
                return {"is_returning_user": False, "prior_summary": "", "last_session_topics": [], "last_session_at": None}

            summary = self._build_summary(all_messages)
            topics = self._extract_topics(all_messages)
            last_at = self._get_last_activity(prior_convs)

            logger.info(
                "SESSION_CONTINUITY: Loaded prior context for user %s — %d messages from %d conversations",
                user_id,
                len(all_messages),
                len(prior_convs),
            )

            return {
                "is_returning_user": True,
                "prior_summary": summary,
                "last_session_topics": topics,
                "last_session_at": last_at,
            }
        except Exception:
            logger.exception("SESSION_CONTINUITY: Failed to load prior session context for user %s", user_id)
            return {"is_returning_user": False, "prior_summary": "", "last_session_topics": [], "last_session_at": None}

    def compress_messages_for_context(
        self,
        messages: List[Dict[str, Any]],
        max_chars: int = _MAX_HISTORY_CHARS,
    ) -> List[Dict[str, Any]]:
        """
        Keep the most recent messages within `max_chars`.

        Older messages that don't fit are replaced with a single summarised
        placeholder so we never silently drop context — AI Mentor always knows
        that earlier conversation happened.
        """
        if not messages:
            return messages

        total_chars = sum(len(m.get("text", "")) for m in messages)
        if total_chars <= max_chars:
            return messages

        # Walk backwards from the end, keeping messages that fit
        kept: List[Dict[str, Any]] = []
        chars_used = 0
        for msg in reversed(messages):
            msg_len = len(msg.get("text", ""))
            if chars_used + msg_len <= max_chars:
                kept.append(msg)
                chars_used += msg_len
            else:
                break

        kept.reverse()
        dropped = len(messages) - len(kept)

        if dropped > 0:
            placeholder = {
                "sender": "system",
                "text": (
                    f"[Earlier conversation: {dropped} message(s) were summarised to save space. "
                    "The conversation above is a continuation of a longer exchange.]"
                ),
                "id": "context_compressed",
            }
            kept = [placeholder] + kept
            logger.info(
                "SESSION_CONTINUITY: Compressed context — kept %d/%d messages (%d chars)",
                len(kept) - 1,
                len(messages),
                chars_used,
            )

        return kept

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_prior_conversations(
        self,
        user_id: str,
        current_conversation_id: Optional[str],
    ) -> List[Conversation]:
        """Fetch the most recent conversations excluding the current one."""
        query = (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .filter(Conversation.status != "deleted")
        )
        if current_conversation_id:
            query = query.filter(Conversation.id != current_conversation_id)

        return (
            query.order_by(Conversation.updated_at.desc())
            .limit(_PRIOR_CONV_LIMIT)
            .all()
        )

    def _build_summary(self, messages: List[Message]) -> str:
        """Build a compact natural-language summary of prior messages."""
        if not messages:
            return ""

        lines = ["Prior conversation summary (for AI Mentor's memory):"]

        user_msgs = [m for m in messages if m.role == "user"]
        bot_msgs = [m for m in messages if m.role == "assistant"]

        if user_msgs:
            lines.append(f"• The user sent {len(user_msgs)} message(s) across previous sessions.")

        # Grab last few user messages for topic context
        recent_user = user_msgs[-5:]
        if recent_user:
            lines.append("• Recent user messages:")
            for m in recent_user:
                snippet = m.content[:120].replace("\n", " ")
                if len(m.content) > 120:
                    snippet += "..."
                lines.append(f"  - {snippet}")

        # Last bot response for continuity
        if bot_msgs:
            last_bot = bot_msgs[-1]
            snippet = last_bot.content[:200].replace("\n", " ")
            if len(last_bot.content) > 200:
                snippet += "..."
            lines.append(f"• Last thing AI Mentor said: {snippet}")

        return "\n".join(lines)

    def _extract_topics(self, messages: List[Message]) -> List[str]:
        """Extract rough topics from user messages (keyword-based, no LLM call)."""
        topic_keywords = {
            "machine learning": ["machine learning", "ml", "neural network", "deep learning", "model"],
            "web development": ["html", "css", "react", "javascript", "frontend", "backend", "web dev"],
            "data science": ["data science", "pandas", "numpy", "data analysis", "statistics"],
            "python": ["python", "django", "flask", "fastapi"],
            "finance": ["finance", "investing", "stocks", "budget", "fintech"],
            "design": ["design", "figma", "ui", "ux", "ui/ux", "prototype"],
            "marketing": ["marketing", "seo", "ads", "campaign", "social media"],
            "learning plan": ["learning plan", "curriculum", "roadmap", "study plan"],
            "career": ["career", "job", "interview", "resume", "portfolio"],
        }

        found: List[str] = []
        user_text = " ".join(
            m.content.lower() for m in messages if m.role == "user"
        )

        for topic, keywords in topic_keywords.items():
            if any(kw in user_text for kw in keywords):
                found.append(topic)

        return found[:5]  # Limit to 5 topics

    def _get_last_activity(self, conversations: List[Conversation]) -> Optional[str]:
        """Return ISO timestamp of the most recent conversation update."""
        if not conversations:
            return None
        latest = max(conversations, key=lambda c: c.updated_at or c.created_at)
        ts = latest.updated_at or latest.created_at
        if ts and not ts.tzinfo:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.isoformat() if ts else None
