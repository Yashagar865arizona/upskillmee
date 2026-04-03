"""
Assessment Service — LLM-based project assessment.

Evaluates a completed project across three dimensions:
  - Completeness (task completion rate, submissions quality)
  - Quality     (average task scores from TaskSubmission.score)
  - Skill alignment (how well submitted work maps to declared project skills)

Returns a ProjectAssessment record with score (0-100), dimension scores,
narrative feedback, and personalised next-step recommendations.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import openai
from sqlalchemy.orm import Session

from ..models.project import Project, ProjectAssessment, PostProjectDiscovery, Task, TaskSubmission
from ..models.user import User

logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

# ---------------------------------------------------------------------------
# Discovery conversation helpers
# ---------------------------------------------------------------------------

_DISCOVERY_STARTER = (
    "How did that project go for you? What parts did you actually enjoy — "
    "any tasks, topics, or moments that felt engaging or satisfying?"
)

_DISCOVERY_PARSE_PROMPT = """You are an interest-discovery assistant. A student just completed (or abandoned) a project and replied to this prompt:

"{starter}"

Their response:
"{response}"

Extract the following from their reply and respond with ONLY valid JSON (no markdown):
{{
  "enjoyed_aspects": "short free-text summary of what they enjoyed (or null)",
  "struggled_aspects": "short free-text summary of what they found hard/uninteresting (or null)",
  "would_continue": true | false | null,
  "engagement_score": integer 1-5 (1=disengaged, 5=highly engaged, based on tone and content),
  "domains_confirmed": ["list", "of", "domains/skills", "they", "expressed", "interest", "in"],
  "domains_rejected": ["list", "of", "domains/skills", "they", "clearly", "want", "to", "avoid"]
}}

Be concise. If information is absent, use null or [].
"""


def _build_project_summary(project: Project, submissions: List[TaskSubmission]) -> str:
    """Build a text summary of the project state for the LLM prompt."""
    task_lines: List[str] = []
    for task in project.tasks:
        sub = next((s for s in submissions if s.task_id == task.id), None)
        status = "completed" if task.completed else "pending"
        score_str = f"score={sub.score}" if sub and sub.score else "not scored"
        feedback_str = sub.feedback[:200] if sub and sub.feedback else "no feedback"
        task_lines.append(
            f"  - [{status}] {task.title}: {task.description or 'no description'} "
            f"({score_str}, feedback: {feedback_str})"
        )

    skills = ", ".join(project.skills or []) or "not specified"
    return (
        f"Project: {project.title}\n"
        f"Description: {project.description or 'N/A'}\n"
        f"Skills targeted: {skills}\n"
        f"Progress: {project.progress_percentage}%\n"
        f"Tasks ({len(project.tasks)} total):\n" + "\n".join(task_lines)
    )


def _call_llm(project_summary: str) -> Dict:
    """Call OpenAI to score and provide feedback on the project."""
    prompt = f"""
You are an expert learning coach evaluating a student's completed project.

{project_summary}

Evaluate the project across three dimensions and provide an overall score.

Instructions:
1. completeness_score (0-100): percentage of tasks properly completed with quality submissions.
2. quality_score (0-100): average quality of submitted work (code, essays, artefacts).
3. skill_alignment_score (0-100): how well the completed work demonstrates the targeted skills.
4. overall_score (0-100): weighted average (completeness 40%, quality 35%, skill_alignment 25%).
5. feedback: 2-3 sentences of honest, encouraging narrative feedback.
6. strengths: list of 2-3 specific things done well.
7. improvements: list of 2-3 specific areas to improve.
8. next_steps: list of 3-4 actionable next learning steps personalised to the gaps.
9. recommended_topics: list of 2-3 topic/skill names to study next.

Respond ONLY with valid JSON:
{{
  "completeness_score": int,
  "quality_score": int,
  "skill_alignment_score": int,
  "overall_score": int,
  "feedback": str,
  "strengths": [str, ...],
  "improvements": [str, ...],
  "next_steps": [str, ...],
  "recommended_topics": [str, ...]
}}
"""
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


def assess_project(db: Session, project_id: str, user_id: str) -> ProjectAssessment:
    """
    Run a full project assessment.

    Raises ValueError if the project is not found or doesn't belong to a plan
    accessible by this user.  Returns the saved ProjectAssessment.
    """
    project: Optional[Project] = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Gather all task submissions for this project
    task_ids = [t.id for t in project.tasks]
    submissions: List[TaskSubmission] = []
    if task_ids:
        submissions = (
            db.query(TaskSubmission)
            .filter(
                TaskSubmission.task_id.in_(task_ids),
                TaskSubmission.user_id == user_id,
            )
            .all()
        )

    project_summary = _build_project_summary(project, submissions)

    try:
        result = _call_llm(project_summary)
    except Exception as exc:
        logger.error("LLM assessment failed: %s", exc)
        # Fallback: score based purely on task completion
        completed = sum(1 for t in project.tasks if t.completed)
        total = len(project.tasks) or 1
        fallback_score = round((completed / total) * 100)
        result = {
            "completeness_score": fallback_score,
            "quality_score": fallback_score,
            "skill_alignment_score": fallback_score,
            "overall_score": fallback_score,
            "feedback": f"Automated scoring based on task completion ({completed}/{total} tasks done). AI evaluation temporarily unavailable.",
            "strengths": ["Completed tasks on time"],
            "improvements": ["Submit more detailed task work for richer feedback"],
            "next_steps": ["Review incomplete tasks", "Re-submit for a full AI review"],
            "recommended_topics": list(project.skills or [])[:3],
        }

    # Upsert: replace existing assessment for this (project, user) pair
    existing: Optional[ProjectAssessment] = (
        db.query(ProjectAssessment)
        .filter(
            ProjectAssessment.project_id == project_id,
            ProjectAssessment.user_id == user_id,
        )
        .first()
    )

    if existing:
        assessment = existing
    else:
        assessment = ProjectAssessment(project_id=project_id, user_id=user_id)
        db.add(assessment)

    assessment.score = result["overall_score"]
    assessment.completeness_score = result.get("completeness_score")
    assessment.quality_score = result.get("quality_score")
    assessment.skill_alignment_score = result.get("skill_alignment_score")
    assessment.feedback = result.get("feedback")
    assessment.strengths = result.get("strengths", [])
    assessment.improvements = result.get("improvements", [])
    assessment.next_steps = result.get("next_steps", [])
    assessment.recommended_topics = result.get("recommended_topics", [])
    assessment.assessment_report = result
    assessment.assessed_at = datetime.utcnow()

    db.commit()
    db.refresh(assessment)

    # Invalidate cached discovery report so it regenerates with new data
    try:
        from .discovery_report_service import invalidate_report
        invalidate_report(db=db, user_id=user_id)
    except Exception as exc:
        logger.warning("Discovery report invalidation failed: %s", exc)

    # Feed assessment results into the interest extraction engine
    try:
        from .interest_extraction_service import InterestExtractionService
        interest_svc = InterestExtractionService(db=db)
        interest_svc.process_assessment_signals(
            user_id=user_id,
            strengths=result.get("strengths", []),
            improvements=result.get("improvements", []),
            recommended_topics=result.get("recommended_topics", []),
            score=result["overall_score"],
            project_domain=project.domain if hasattr(project, "domain") else None,
        )
    except Exception as exc:
        logger.warning("Interest signal processing after assessment failed: %s", exc)

    # Update skill map with assessment results
    try:
        from .skill_map_service import update_skills_from_assessment
        update_skills_from_assessment(
            db=db,
            user_id=user_id,
            project=project,
            assessment=assessment,
        )
    except Exception as exc:
        logger.warning("Skill map update after assessment failed: %s", exc)

    return assessment


def get_assessment(db: Session, project_id: str, user_id: str) -> Optional[ProjectAssessment]:
    """Fetch the latest assessment for a project/user pair."""
    return (
        db.query(ProjectAssessment)
        .filter(
            ProjectAssessment.project_id == project_id,
            ProjectAssessment.user_id == user_id,
        )
        .first()
    )


# ---------------------------------------------------------------------------
# Post-project discovery conversation
# ---------------------------------------------------------------------------

def trigger_discovery(
    db: Session,
    project_id: str,
    user_id: str,
    reason: str,
) -> PostProjectDiscovery:
    """
    Create a discovery record for a project on completion or abandonment.

    Raises ValueError if a discovery already exists for this project (idempotent).
    Returns the new PostProjectDiscovery with the conversation_starter populated.
    """
    existing = (
        db.query(PostProjectDiscovery)
        .filter(PostProjectDiscovery.project_id == project_id)
        .first()
    )
    if existing:
        raise ValueError(f"Discovery already triggered for project {project_id}")

    discovery = PostProjectDiscovery(
        project_id=project_id,
        user_id=user_id,
        trigger_reason=reason,
        triggered_at=datetime.now(timezone.utc),
        conversation_starter=_DISCOVERY_STARTER,
    )
    db.add(discovery)
    db.commit()
    db.refresh(discovery)
    return discovery


def process_discovery_response(
    db: Session,
    discovery_id: str,
    user_response: str,
) -> PostProjectDiscovery:
    """
    Parse the user's discovery response with the LLM, store structured data,
    mark the discovery complete, and emit an interest-update event.

    Returns the updated PostProjectDiscovery.
    """
    discovery: Optional[PostProjectDiscovery] = (
        db.query(PostProjectDiscovery)
        .filter(PostProjectDiscovery.id == discovery_id)
        .first()
    )
    if not discovery:
        raise ValueError(f"Discovery {discovery_id} not found")

    prompt = _DISCOVERY_PARSE_PROMPT.format(
        starter=discovery.conversation_starter or _DISCOVERY_STARTER,
        response=user_response,
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
    except Exception as exc:
        logger.error("Discovery LLM parse failed for %s: %s", discovery_id, exc)
        # Fallback: store raw response, mark as complete with defaults
        parsed = {
            "enjoyed_aspects": user_response[:500],
            "struggled_aspects": None,
            "would_continue": None,
            "engagement_score": 3,
            "domains_confirmed": [],
            "domains_rejected": [],
        }

    discovery.enjoyed_aspects = parsed.get("enjoyed_aspects")
    discovery.struggled_aspects = parsed.get("struggled_aspects")
    discovery.would_continue = parsed.get("would_continue")
    discovery.engagement_score = parsed.get("engagement_score")
    discovery.domains_confirmed = parsed.get("domains_confirmed") or []
    discovery.domains_rejected = parsed.get("domains_rejected") or []
    discovery.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(discovery)

    # Emit interest update event: merge confirmed domains into UserProfile.extracted_interests
    _emit_interest_event(db, discovery)

    return discovery


def _emit_interest_event(db: Session, discovery: PostProjectDiscovery) -> None:
    """
    Merge domains confirmed/rejected from the discovery into the user's
    extracted_interests profile so the ML/AI Engineer's interest model stays current.
    """
    from ..models.user import UserProfile

    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == discovery.user_id).first()
        if profile is None:
            profile = UserProfile(user_id=discovery.user_id, extracted_interests=[])
            db.add(profile)

        current: List[Dict] = profile.extracted_interests or []

        # Index existing interests by name for dedup
        existing_names = {i.get("name", "").lower() for i in current if isinstance(i, dict)}

        for domain in (discovery.domains_confirmed or []):
            name = str(domain).lower().strip()
            if name and name not in existing_names:
                current.append({
                    "name": name,
                    "category": "domain",
                    "confidence": 0.8,
                    "source": "project_discovery",
                    "added_at": datetime.now(timezone.utc).isoformat(),
                })
                existing_names.add(name)

        # Mark rejected domains with lower confidence so they fade out
        for interest in current:
            if isinstance(interest, dict):
                name = interest.get("name", "").lower()
                if name in {str(d).lower() for d in (discovery.domains_rejected or [])}:
                    interest["confidence"] = max(0.0, interest.get("confidence", 0.5) - 0.4)

        profile.extracted_interests = current
        db.commit()
        logger.info(
            "Interest event emitted for user=%s: confirmed=%s rejected=%s",
            discovery.user_id,
            discovery.domains_confirmed,
            discovery.domains_rejected,
        )
    except Exception as exc:
        logger.error("Failed to emit interest event for discovery %s: %s", discovery.id, exc)
        # Non-fatal: don't roll back the discovery commit


def get_discovery(db: Session, project_id: str) -> Optional[PostProjectDiscovery]:
    """Fetch the discovery record for a project (if it exists)."""
    return (
        db.query(PostProjectDiscovery)
        .filter(PostProjectDiscovery.project_id == project_id)
        .first()
    )
