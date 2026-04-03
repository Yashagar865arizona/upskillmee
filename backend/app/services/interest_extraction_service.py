"""
Interest Extraction Service

Extracts user interests from natural conversation using LLM and stores them
durably in the user profile. Supports deduplication and incremental merging.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..config import settings
from ..models.user import UserProfile

logger = logging.getLogger(__name__)

# Categories that signal an extractable interest
INTEREST_CATEGORIES = {
    "technical": [
        "game dev", "game development", "web dev", "web development", "mobile dev",
        "machine learning", "ml", "ai", "artificial intelligence", "data science",
        "backend", "frontend", "fullstack", "devops", "cloud", "blockchain",
        "cybersecurity", "embedded", "systems programming", "open source",
        "python", "javascript", "rust", "go", "java", "c++", "typescript",
        "react", "node", "django", "fastapi", "kubernetes", "docker",
        "databases", "sql", "nosql", "apis", "microservices",
    ],
    "career": [
        "startup", "startups", "entrepreneur", "entrepreneurship", "freelance",
        "product management", "project management", "consulting", "leadership",
        "remote work", "business", "finance", "marketing", "sales",
        "research", "academia", "teaching", "content creation",
    ],
    "creative": [
        "design", "ui", "ux", "graphic design", "3d modeling", "animation",
        "music", "art", "writing", "storytelling", "video", "photography",
        "game design", "worldbuilding",
    ],
    "domain": [
        "healthcare", "education", "edtech", "fintech", "e-commerce",
        "social impact", "sustainability", "climate", "space", "robotics",
        "iot", "ar", "vr", "metaverse", "crypto", "nft",
    ],
}

EXTRACTION_SYSTEM_PROMPT = """You are an interest-extraction assistant.

Given a single user message from a learning/mentoring chat, identify any explicit or strongly
implied interest signals. An interest signal is something the user WANTS to learn, build,
work on, or is enthusiastic about — not just a topic they mention in passing.

Return a JSON array of interest objects. Each object has:
  - "name": concise interest label (2-5 words, lowercase, e.g. "game development")
  - "category": one of "technical", "career", "creative", "domain", "other"
  - "confidence": float 0.0-1.0 (how certain you are this is a real interest)

Only return interests with confidence >= 0.6. Return an empty array [] if none found.

Respond with ONLY the JSON array — no explanation, no markdown fences.
"""


class InterestExtractionService:
    """Extracts and persists user interests from chat messages using an LLM pass."""

    def __init__(self, db: Session):
        self.db = db
        self._client: Optional[Any] = None

    def _get_client(self) -> Any:
        """Lazy-init OpenAI async client."""
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def extract_and_store(self, user_id: str, message: str) -> List[Dict]:
        """
        Run LLM extraction on *message*, merge with existing interests, persist.

        Returns the updated interests list for the user.
        """
        try:
            raw = await self._llm_extract(message)
            if not raw:
                return self._load_interests(user_id)
            merged = self._merge_interests(self._load_interests(user_id), raw)
            self._save_interests(user_id, merged)
            logger.info(
                "Interest extraction: user=%s message_len=%d extracted=%d total=%d",
                user_id,
                len(message),
                len(raw),
                len(merged),
            )
            return merged
        except Exception as exc:
            logger.error("Interest extraction failed for user=%s: %s", user_id, exc)
            return self._load_interests(user_id)

    def get_interests(self, user_id: str) -> List[Dict]:
        """Return persisted interests for a user (no LLM call)."""
        return self._load_interests(user_id)

    def get_interests_as_strings(self, user_id: str) -> List[str]:
        """Return interest names as a flat list of strings."""
        return [i["name"] for i in self._load_interests(user_id)]

    # ------------------------------------------------------------------
    # LLM extraction
    # ------------------------------------------------------------------

    async def _llm_extract(self, message: str) -> List[Dict]:
        """Call the LLM and parse its response into interest dicts."""
        client = self._get_client()
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                temperature=0.0,
                max_tokens=512,
            )
            raw_text = response.choices[0].message.content.strip()
            interests = json.loads(raw_text)
            if not isinstance(interests, list):
                return []
            validated = []
            for item in interests:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).strip().lower()
                category = str(item.get("category", "other")).strip().lower()
                confidence = float(item.get("confidence", 0.0))
                if name and confidence >= 0.6:
                    validated.append(
                        {
                            "name": name,
                            "category": category if category in INTEREST_CATEGORIES else "other",
                            "confidence": round(confidence, 2),
                        }
                    )
            return validated
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("Could not parse LLM interest extraction response: %s", exc)
            return []

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _load_interests(self, user_id: str) -> List[Dict]:
        """Load current extracted_interests from UserProfile."""
        profile = (
            self.db.query(UserProfile)
            .filter(UserProfile.user_id == user_id)
            .first()
        )
        if profile is None or profile.extracted_interests is None:
            return []
        data = profile.extracted_interests
        if isinstance(data, list):
            return data
        return []

    def _save_interests(self, user_id: str, interests: List[Dict]) -> None:
        """Persist the merged interest list back to UserProfile."""
        profile = (
            self.db.query(UserProfile)
            .filter(UserProfile.user_id == user_id)
            .first()
        )
        if profile is None:
            profile = UserProfile(user_id=user_id, extracted_interests=interests)
            self.db.add(profile)
        else:
            profile.extracted_interests = interests
        self.db.commit()

    # ------------------------------------------------------------------
    # Merging logic
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_interests(
        existing: List[Dict], new_signals: List[Dict]
    ) -> List[Dict]:
        """
        Merge new_signals into existing.

        - Deduplicate by name (case-insensitive).
        - On collision: keep the higher confidence, increment seen count,
          update last_seen_at.
        - New interests are appended with count=1 and last_seen_at=now.
        """
        now = datetime.now(timezone.utc).isoformat()
        index: Dict[str, Dict] = {i["name"].lower(): i for i in existing}

        for signal in new_signals:
            key = signal["name"].lower()
            if key in index:
                entry = index[key]
                # Keep highest confidence seen so far
                entry["confidence"] = max(entry["confidence"], signal["confidence"])
                entry["count"] = entry.get("count", 1) + 1
                entry["last_seen_at"] = now
            else:
                index[key] = {
                    "name": signal["name"],
                    "category": signal["category"],
                    "confidence": signal["confidence"],
                    "count": 1,
                    "last_seen_at": now,
                }

        return list(index.values())
