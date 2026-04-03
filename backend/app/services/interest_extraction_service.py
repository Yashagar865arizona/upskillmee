"""
Interest Extraction Service

Extracts user interests from natural conversation using LLM and stores them
in two complementary structures:
  1. UserProfile.extracted_interests — flat list of {name, category, confidence, count}
     for backward-compat and quick keyword retrieval.
  2. UserInterestProfile — structured profile with domains (weighted dict),
     strengths, aversions, learning_style, confidence_level, and signal_count.

Signal sources handled here:
  - Conversation signals (real-time, per message)
  - Project assessment signals (post-assessment)
  - Behavioral signals (project completion events)
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..config import settings
from ..models.user import UserProfile, UserInterestProfile

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

Given a user message from a learning/mentoring chat, identify explicit or strongly
implied signals about the user's interests, strengths, and dislikes.

Return a JSON object with these keys:
  - "domains": object mapping domain names (2-5 words, lowercase) to confidence (0.0-1.0)
    e.g. {"game development": 0.9, "startup building": 0.75}
    Only include domains the user WANTS to learn, build, or work on (confidence >= 0.6).
  - "strengths": list of 2-4 word strings for abilities the user describes positively
    e.g. ["creative thinking", "visual design", "problem solving"]
    Empty list if none found.
  - "aversions": list of 2-4 word strings for things the user explicitly dislikes or avoids
    e.g. ["repetitive tasks", "backend plumbing"]
    Empty list if none found.
  - "learning_style": one of "hands-on", "conceptual", "mixed", or null if not inferable.

Respond with ONLY the JSON object — no explanation, no markdown fences.
Example: {"domains": {"game development": 0.9}, "strengths": ["creative thinking"], "aversions": [], "learning_style": "hands-on"}
"""


class InterestExtractionService:
    """Extracts and persists user interests from chat messages and assessment results."""

    def __init__(self, db: Session):
        self.db = db
        self._client: Optional[Any] = None

    def _get_client(self) -> Any:
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

        Returns the updated extracted_interests list (backward-compat flat list).
        """
        try:
            raw = await self._llm_extract_structured(message)
            if not raw:
                return self._load_interests(user_id)

            # Update flat list (backward-compat)
            flat_signals = [
                {"name": domain, "category": self._categorize(domain), "confidence": conf}
                for domain, conf in raw.get("domains", {}).items()
            ]
            merged_flat = self._merge_interests(self._load_interests(user_id), flat_signals)
            self._save_interests(user_id, merged_flat)

            # Update structured profile
            self._update_structured_profile(user_id, raw)

            logger.info(
                "Interest extraction: user=%s message_len=%d domains=%d",
                user_id, len(message), len(raw.get("domains", {})),
            )
            return merged_flat
        except Exception as exc:
            logger.error("Interest extraction failed for user=%s: %s", user_id, exc)
            return self._load_interests(user_id)

    def process_assessment_signals(
        self,
        user_id: str,
        strengths: List[str],
        improvements: List[str],
        recommended_topics: List[str],
        score: int,
        project_domain: Optional[str] = None,
    ) -> None:
        """
        Update interest profile from a completed project assessment.

        - High score + strengths → boost domain, add to strengths
        - Low score (< 40) → weak aversion signal on domain
        - Recommended topics → add as medium-confidence domains
        """
        try:
            profile = self._get_or_create_structured_profile(user_id)
            domains = dict(profile.domains or {})
            existing_strengths = list(profile.strengths or [])
            existing_aversions = list(profile.aversions or [])

            # Boost or add project domain
            if project_domain:
                domain_key = project_domain.lower().strip()
                if score >= 70:
                    domains[domain_key] = min(1.0, domains.get(domain_key, 0.0) + 0.2)
                elif score < 40:
                    if domain_key not in existing_aversions:
                        existing_aversions.append(domain_key)

            # Strengths from assessment → add to profile strengths
            for s in strengths:
                s_clean = s.strip()[:80]
                if s_clean and s_clean not in existing_strengths:
                    existing_strengths.append(s_clean)

            # Recommended topics → add as domains with medium confidence
            for topic in recommended_topics:
                t_key = topic.lower().strip()
                if t_key and t_key not in domains:
                    domains[t_key] = 0.5

            profile.domains = domains
            profile.strengths = existing_strengths[:20]
            profile.aversions = existing_aversions[:10]
            profile.signal_count = (profile.signal_count or 0) + 1
            profile.confidence_level = min(1.0, (profile.signal_count / 10.0))

            self.db.commit()
            logger.info("Assessment signals processed for user=%s score=%d", user_id, score)
        except Exception as exc:
            logger.error("Assessment signal processing failed for user=%s: %s", user_id, exc)
            self.db.rollback()

    def process_behavioral_signal(
        self,
        user_id: str,
        signal_type: str,
        domain: Optional[str] = None,
    ) -> None:
        """
        Process a behavioral signal about the user's engagement.

        signal_type:
          "project_abandoned_early"  → weak negative signal for domain
          "project_completed_fast"   → strong strength signal for domain
          "followup_questions_asked" → interest signal for domain
        """
        if not domain:
            return
        try:
            profile = self._get_or_create_structured_profile(user_id)
            domains = dict(profile.domains or {})
            d_key = domain.lower().strip()

            if signal_type == "project_abandoned_early":
                existing = domains.get(d_key, 0.5)
                domains[d_key] = max(0.0, existing - 0.1)
            elif signal_type == "project_completed_fast":
                domains[d_key] = min(1.0, domains.get(d_key, 0.0) + 0.25)
            elif signal_type == "followup_questions_asked":
                domains[d_key] = min(1.0, domains.get(d_key, 0.0) + 0.15)

            profile.domains = domains
            profile.signal_count = (profile.signal_count or 0) + 1
            profile.confidence_level = min(1.0, (profile.signal_count / 10.0))
            self.db.commit()
        except Exception as exc:
            logger.error("Behavioral signal failed for user=%s: %s", user_id, exc)
            self.db.rollback()

    def get_interests(self, user_id: str) -> List[Dict]:
        """Return persisted flat interests for a user (no LLM call)."""
        return self._load_interests(user_id)

    def get_interests_as_strings(self, user_id: str) -> List[str]:
        """Return interest names as a flat list of strings."""
        return [i["name"] for i in self._load_interests(user_id)]

    def get_structured_profile(self, user_id: str) -> Optional[Dict]:
        """Return the structured interest profile dict or None."""
        profile = self._get_structured_profile_model(user_id)
        if profile is None:
            return None
        return {
            "domains": profile.domains or {},
            "strengths": profile.strengths or [],
            "aversions": profile.aversions or [],
            "learning_style": profile.learning_style,
            "confidence_level": profile.confidence_level or 0.0,
            "signal_count": profile.signal_count or 0,
        }

    def reset_interest_profile(self, user_id: str) -> None:
        """Clear all interest data for a user (both flat and structured)."""
        try:
            user_profile = self._get_user_profile(user_id)
            if user_profile:
                user_profile.extracted_interests = []
                struct = self._get_structured_profile_model(user_id)
                if struct:
                    struct.domains = {}
                    struct.strengths = []
                    struct.aversions = []
                    struct.learning_style = None
                    struct.confidence_level = 0.0
                    struct.signal_count = 0
                self.db.commit()
        except Exception as exc:
            logger.error("Reset interest profile failed for user=%s: %s", user_id, exc)
            self.db.rollback()

    # ------------------------------------------------------------------
    # LLM extraction
    # ------------------------------------------------------------------

    async def _llm_extract_structured(self, message: str) -> Optional[Dict]:
        """Call the LLM and return a structured dict with domains/strengths/aversions."""
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
            data = json.loads(raw_text)
            if not isinstance(data, dict):
                return None

            result: Dict[str, Any] = {
                "domains": {},
                "strengths": [],
                "aversions": [],
                "learning_style": None,
            }
            for domain, conf in data.get("domains", {}).items():
                try:
                    c = float(conf)
                    if c >= 0.6:
                        result["domains"][str(domain).lower().strip()] = round(c, 2)
                except (ValueError, TypeError):
                    pass
            result["strengths"] = [
                str(s).strip() for s in data.get("strengths", [])
                if isinstance(s, str) and s.strip()
            ][:10]
            result["aversions"] = [
                str(a).strip() for a in data.get("aversions", [])
                if isinstance(a, str) and a.strip()
            ][:10]
            ls = data.get("learning_style")
            if ls in ("hands-on", "conceptual", "mixed"):
                result["learning_style"] = ls

            if not result["domains"] and not result["strengths"] and not result["aversions"]:
                return None
            return result
        except (json.JSONDecodeError, KeyError, ValueError, AttributeError) as exc:
            logger.warning("Could not parse LLM interest extraction response: %s", exc)
            return None

    async def _llm_extract(self, message: str) -> List[Dict]:
        """Legacy method — returns flat list of interest dicts (backward-compat)."""
        result = await self._llm_extract_structured(message)
        if not result:
            return []
        return [
            {
                "name": domain,
                "category": self._categorize(domain),
                "confidence": conf,
            }
            for domain, conf in result.get("domains", {}).items()
        ]

    # ------------------------------------------------------------------
    # DB helpers — flat list
    # ------------------------------------------------------------------

    def _get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        return (
            self.db.query(UserProfile)
            .filter(UserProfile.user_id == user_id)
            .first()
        )

    def _load_interests(self, user_id: str) -> List[Dict]:
        profile = self._get_user_profile(user_id)
        if profile is None or profile.extracted_interests is None:
            return []
        data = profile.extracted_interests
        return data if isinstance(data, list) else []

    def _save_interests(self, user_id: str, interests: List[Dict]) -> None:
        profile = self._get_user_profile(user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id, extracted_interests=interests)
            self.db.add(profile)
        else:
            profile.extracted_interests = interests
        self.db.commit()

    # ------------------------------------------------------------------
    # DB helpers — structured profile
    # ------------------------------------------------------------------

    def _get_structured_profile_model(self, user_id: str) -> Optional[UserInterestProfile]:
        user_profile = self._get_user_profile(user_id)
        if user_profile is None:
            return None
        return (
            self.db.query(UserInterestProfile)
            .filter(UserInterestProfile.user_profile_id == user_profile.id)
            .first()
        )

    def _get_or_create_structured_profile(self, user_id: str) -> UserInterestProfile:
        user_profile = self._get_user_profile(user_id)
        if user_profile is None:
            user_profile = UserProfile(user_id=user_id, extracted_interests=[])
            self.db.add(user_profile)
            self.db.flush()

        existing = (
            self.db.query(UserInterestProfile)
            .filter(UserInterestProfile.user_profile_id == user_profile.id)
            .first()
        )
        if existing:
            return existing

        new_profile = UserInterestProfile(
            user_profile_id=user_profile.id,
            domains={},
            strengths=[],
            aversions=[],
            learning_style=None,
            confidence_level=0.0,
            signal_count=0,
        )
        self.db.add(new_profile)
        self.db.flush()
        return new_profile

    def _update_structured_profile(self, user_id: str, raw: Dict) -> None:
        """Merge extracted structured data into the UserInterestProfile."""
        profile = self._get_or_create_structured_profile(user_id)

        # Merge domains with weighted update
        domains = dict(profile.domains or {})
        for domain, conf in raw.get("domains", {}).items():
            existing = domains.get(domain, 0.0)
            # Keep highest confidence with a slight nudge from the new signal
            domains[domain] = round(min(1.0, max(existing, conf) * 0.9 + conf * 0.1), 3)
        profile.domains = domains

        # Merge strengths (deduplicate, cap at 20)
        strengths = list(profile.strengths or [])
        for s in raw.get("strengths", []):
            if s not in strengths:
                strengths.append(s)
        profile.strengths = strengths[:20]

        # Merge aversions (deduplicate, cap at 10)
        aversions = list(profile.aversions or [])
        for a in raw.get("aversions", []):
            if a not in aversions:
                aversions.append(a)
        profile.aversions = aversions[:10]

        if raw.get("learning_style"):
            profile.learning_style = raw["learning_style"]

        profile.signal_count = (profile.signal_count or 0) + 1
        profile.confidence_level = round(min(1.0, (profile.signal_count / 10.0)), 3)

        self.db.commit()

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _categorize(domain: str) -> str:
        d = domain.lower()
        for category, keywords in INTEREST_CATEGORIES.items():
            if any(kw in d for kw in keywords):
                return category
        return "other"

    @staticmethod
    def _merge_interests(
        existing: List[Dict], new_signals: List[Dict]
    ) -> List[Dict]:
        """
        Merge new_signals into existing flat list.
        Deduplicate by name, keep highest confidence, increment count.
        """
        now = datetime.now(timezone.utc).isoformat()
        index: Dict[str, Dict] = {i["name"].lower(): i for i in existing}

        for signal in new_signals:
            key = signal["name"].lower()
            if key in index:
                entry = index[key]
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
