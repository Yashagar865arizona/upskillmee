"""
Session continuity service — loads prior conversation context so the AI Mentor can
resume naturally when a user returns.

Responsibilities:
- Generate AI-powered structured summaries when sessions end
- Load stored summaries from the sessions table for returning users
- Fall back to raw message scan when stored summaries don't exist
- Compress long in-session histories to stay within token limits
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models.chat import Conversation, Message
from ..models.chat import Session as ChatSession

logger = logging.getLogger(__name__)

# Approximate characters per token (conservative estimate for GPT-4)
_CHARS_PER_TOKEN = 4
# Max tokens to spend on history before compressing
_MAX_HISTORY_TOKENS = 2000
_MAX_HISTORY_CHARS = _MAX_HISTORY_TOKENS * _CHARS_PER_TOKEN

# How many prior sessions to pull stored summaries from
_PRIOR_SESSION_LIMIT = 3
# How many prior conversations to scan when no stored summaries exist (fallback)
_PRIOR_CONV_LIMIT = 3
# How many messages to pull from each prior conversation in fallback mode
_PRIOR_MSGS_PER_CONV = 20

# Target summary length in characters (~200 tokens)
_SUMMARY_MAX_CHARS = 800


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

        Prefers stored AI summaries from the sessions table.  Falls back to
        raw message scanning when no stored summaries are available.

        Keys:
            is_returning_user (bool)
            prior_summary (str)         — formatted for the system prompt
            last_session_topics (list)  — key topics from last session
            last_session_at (str|None)  — ISO timestamp of last activity
        """
        try:
            # --- Preferred path: stored AI summaries ---
            stored_ctx = self._load_from_stored_summaries(user_id)
            if stored_ctx["is_returning_user"]:
                return stored_ctx

            # --- Fallback path: raw message scan ---
            prior_convs = self._get_prior_conversations(user_id, current_conversation_id)
            if not prior_convs:
                return {
                    "is_returning_user": False,
                    "prior_summary": "",
                    "last_session_topics": [],
                    "last_session_at": None,
                }

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
                return {
                    "is_returning_user": False,
                    "prior_summary": "",
                    "last_session_topics": [],
                    "last_session_at": None,
                }

            summary = self._build_raw_summary(all_messages)
            topics = self._extract_topics(all_messages)
            last_at = self._get_last_activity(prior_convs)

            logger.info(
                "SESSION_CONTINUITY: Fallback raw scan for user %s — %d messages from %d conversations",
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
            logger.exception(
                "SESSION_CONTINUITY: Failed to load prior session context for user %s", user_id
            )
            return {
                "is_returning_user": False,
                "prior_summary": "",
                "last_session_topics": [],
                "last_session_at": None,
            }

    def generate_and_store_summary(self, session_id: str) -> bool:
        """
        Generate an AI summary of *session_id* and persist it to the DB.

        Should be called as a background task after a session ends.
        Returns True on success, False on failure (never raises).
        """
        try:
            session = (
                self.db.query(ChatSession)
                .filter(ChatSession.id == session_id)
                .first()
            )
            if not session:
                logger.warning(
                    "SESSION_CONTINUITY: Session %s not found for summarisation", session_id
                )
                return False

            # Collect all messages in this session
            messages = (
                self.db.query(Message)
                .filter(Message.session_id == session_id)
                .order_by(Message.created_at.asc())
                .all()
            )

            if not messages:
                logger.info(
                    "SESSION_CONTINUITY: Session %s has no messages — skipping summary", session_id
                )
                return False

            summary_text = self._generate_ai_summary(messages)
            if not summary_text:
                return False

            session.summary = summary_text
            session.summarized_at = datetime.utcnow()
            self.db.commit()

            logger.info(
                "SESSION_CONTINUITY: Stored AI summary for session %s (%d chars)",
                session_id,
                len(summary_text),
            )
            return True

        except Exception:
            logger.exception(
                "SESSION_CONTINUITY: Failed to generate summary for session %s", session_id
            )
            try:
                self.db.rollback()
            except Exception:
                pass
            return False

    def compress_messages_for_context(
        self,
        messages: List[Dict[str, Any]],
        max_chars: int = _MAX_HISTORY_CHARS,
    ) -> List[Dict[str, Any]]:
        """
        Keep the most recent messages within `max_chars`.

        Older messages that don't fit are replaced with a single summarised
        placeholder so we never silently drop context.
        """
        if not messages:
            return messages

        total_chars = sum(len(m.get("text", "")) for m in messages)
        if total_chars <= max_chars:
            return messages

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
    # Private helpers — stored summary path
    # ------------------------------------------------------------------

    def _load_from_stored_summaries(self, user_id: str) -> Dict[str, Any]:
        """Load the most recent summarised sessions for this user."""
        recent_sessions = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.user_id == user_id,
                ChatSession.summary.isnot(None),
                ChatSession.ended_at.isnot(None),
            )
            .order_by(ChatSession.ended_at.desc())
            .limit(_PRIOR_SESSION_LIMIT)
            .all()
        )

        if not recent_sessions:
            return {
                "is_returning_user": False,
                "prior_summary": "",
                "last_session_topics": [],
                "last_session_at": None,
            }

        # Combine summaries, most recent first
        combined_parts = ["Prior session summaries (for AI Mentor's memory):"]
        all_topics: List[str] = []

        for i, sess in enumerate(recent_sessions):
            label = "Most recent session" if i == 0 else f"Earlier session {i}"
            combined_parts.append(f"\n[{label}]\n{sess.summary}")
            all_topics.extend(self._extract_topics_from_text(sess.summary or ""))

        prior_summary = "\n".join(combined_parts)

        last_at_raw = recent_sessions[0].ended_at
        if last_at_raw and not last_at_raw.tzinfo:
            last_at_raw = last_at_raw.replace(tzinfo=timezone.utc)
        last_session_at = last_at_raw.isoformat() if last_at_raw else None

        # Deduplicate topics preserving order
        seen: set = set()
        unique_topics = [t for t in all_topics if not (t in seen or seen.add(t))]  # type: ignore[func-returns-value]

        logger.info(
            "SESSION_CONTINUITY: Loaded %d stored summaries for user %s",
            len(recent_sessions),
            user_id,
        )

        return {
            "is_returning_user": True,
            "prior_summary": prior_summary,
            "last_session_topics": unique_topics[:5],
            "last_session_at": last_session_at,
        }

    def _generate_ai_summary(self, messages: List[Message]) -> str:
        """Call OpenAI to produce a structured ~200-token session summary."""
        try:
            from openai import OpenAI
            from ..config import settings
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception:
            logger.warning(
                "SESSION_CONTINUITY: OpenAI client unavailable — using rule-based summary"
            )
            return self._build_raw_summary(messages)

        # Build compact transcript (last 30 messages to cap input cost)
        transcript_lines = []
        for m in messages[-30:]:
            role = "User" if m.role == "user" else "Mentor"
            snippet = m.content[:200].replace("\n", " ")
            transcript_lines.append(f"{role}: {snippet}")
        transcript = "\n".join(transcript_lines)

        system_prompt = (
            "You are a memory assistant for an AI learning mentor. "
            "Given a conversation transcript, produce a concise structured summary "
            "(at most 200 tokens) covering:\n"
            "• What the user was working on or learning\n"
            "• Key decisions or goals set\n"
            "• The user's emotional tone (motivated, frustrated, curious, etc.)\n"
            "• Open threads — things the user said they'd do or return to\n\n"
            "Be specific and factual. Write in third person about the user."
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Conversation transcript:\n{transcript}"},
                ],
                max_tokens=250,
                temperature=0.3,
            )
            summary = response.choices[0].message.content or ""
            return summary[:_SUMMARY_MAX_CHARS]
        except Exception:
            logger.exception(
                "SESSION_CONTINUITY: OpenAI summary call failed — falling back to rule-based"
            )
            return self._build_raw_summary(messages)

    # ------------------------------------------------------------------
    # Private helpers — fallback raw message path
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

    def _build_raw_summary(self, messages: List[Message]) -> str:
        """Build a compact natural-language summary of prior messages without an LLM call."""
        if not messages:
            return ""

        lines = ["Prior conversation summary (for AI Mentor's memory):"]

        user_msgs = [m for m in messages if m.role == "user"]
        bot_msgs = [m for m in messages if m.role == "assistant"]

        if user_msgs:
            lines.append(f"• The user sent {len(user_msgs)} message(s) across previous sessions.")

        recent_user = user_msgs[-5:]
        if recent_user:
            lines.append("• Recent user messages:")
            for m in recent_user:
                snippet = m.content[:120].replace("\n", " ")
                if len(m.content) > 120:
                    snippet += "..."
                lines.append(f"  - {snippet}")

        if bot_msgs:
            last_bot = bot_msgs[-1]
            snippet = last_bot.content[:200].replace("\n", " ")
            if len(last_bot.content) > 200:
                snippet += "..."
            lines.append(f"• Last thing AI Mentor said: {snippet}")

        return "\n".join(lines)

    def _extract_topics(self, messages: List[Message]) -> List[str]:
        """Extract rough topics from user messages (keyword-based)."""
        user_text = " ".join(m.content.lower() for m in messages if m.role == "user")
        return self._extract_topics_from_text(user_text)

    def _extract_topics_from_text(self, text: str) -> List[str]:
        """Extract topics from a free-text string."""
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
        lowered = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in lowered for kw in keywords):
                found.append(topic)
        return found[:5]

    def _get_last_activity(self, conversations: List[Conversation]) -> Optional[str]:
        if not conversations:
            return None
        latest = max(conversations, key=lambda c: c.updated_at or c.created_at)
        ts = latest.updated_at or latest.created_at
        if ts and not ts.tzinfo:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.isoformat() if ts else None
