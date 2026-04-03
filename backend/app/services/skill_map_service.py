"""
Skill Map Service — tracks, scores, and clusters user skills.

After each project assessment the caller invokes `update_skills_from_assessment`
which upserts UserSkill rows.  `get_skill_map` returns a graph-ready payload
(nodes = skills, edges = co-occurrence, size = proficiency).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models.project import Project, ProjectAssessment
from ..models.user import UserInterestProfile, UserProfile, UserSkill

logger = logging.getLogger(__name__)

# ── Domain clustering: keyword → domain label ──────────────────────────────
# Extensible lookup — keeps things fast without needing embeddings for MVP.
_DOMAIN_MAP: Dict[str, str] = {
    # Web Dev
    "html": "Web Dev", "css": "Web Dev", "javascript": "Web Dev",
    "typescript": "Web Dev", "react": "Web Dev", "vue": "Web Dev",
    "angular": "Web Dev", "next.js": "Web Dev", "nextjs": "Web Dev",
    "svelte": "Web Dev", "tailwind": "Web Dev", "sass": "Web Dev",
    "webpack": "Web Dev", "node": "Web Dev", "node.js": "Web Dev",
    "express": "Web Dev", "fastapi": "Web Dev", "django": "Web Dev",
    "flask": "Web Dev", "rest api": "Web Dev", "graphql": "Web Dev",
    # Data Science / ML
    "python": "Data Science", "pandas": "Data Science",
    "numpy": "Data Science", "matplotlib": "Data Science",
    "scikit-learn": "Data Science", "sklearn": "Data Science",
    "tensorflow": "ML/AI", "pytorch": "ML/AI", "keras": "ML/AI",
    "machine learning": "ML/AI", "deep learning": "ML/AI",
    "nlp": "ML/AI", "computer vision": "ML/AI",
    "data analysis": "Data Science", "data cleaning": "Data Science",
    "statistics": "Data Science", "sql": "Data Science",
    "data visualization": "Data Science",
    # Mobile
    "react native": "Mobile", "flutter": "Mobile", "swift": "Mobile",
    "kotlin": "Mobile", "android": "Mobile", "ios": "Mobile",
    # DevOps / Cloud
    "docker": "DevOps", "kubernetes": "DevOps", "aws": "Cloud",
    "azure": "Cloud", "gcp": "Cloud", "ci/cd": "DevOps",
    "terraform": "DevOps", "linux": "DevOps", "git": "DevOps",
    # Game Dev
    "unity": "Game Dev", "unreal": "Game Dev", "godot": "Game Dev",
    "game design": "Game Dev", "c#": "Game Dev",
    # General CS
    "algorithms": "CS Fundamentals", "data structures": "CS Fundamentals",
    "oop": "CS Fundamentals", "design patterns": "CS Fundamentals",
    "databases": "CS Fundamentals", "networking": "CS Fundamentals",
}


def _classify_domain(skill_name: str) -> str:
    """Return a domain label for a skill name using keyword matching."""
    key = skill_name.lower().strip()
    if key in _DOMAIN_MAP:
        return _DOMAIN_MAP[key]
    # Partial match fallback
    for keyword, domain in _DOMAIN_MAP.items():
        if keyword in key or key in keyword:
            return domain
    return "General"


def _compute_proficiency(total_score: int, assessment_count: int) -> float:
    """
    Proficiency 0.0–1.0 based on average assessment score and repetition.

    Formula: base = avg_score / 100, bonus = min(0.1, count * 0.02)
    Capped at 1.0.
    """
    if assessment_count == 0:
        return 0.0
    avg = total_score / assessment_count  # 0-100 scale
    base = avg / 100.0
    repetition_bonus = min(0.1, assessment_count * 0.02)
    return min(1.0, round(base + repetition_bonus, 3))


# ── Public API ─────────────────────────────────────────────────────────────


def update_skills_from_assessment(
    db: Session,
    user_id: str,
    project: Project,
    assessment: ProjectAssessment,
) -> List[UserSkill]:
    """
    Upsert UserSkill rows after a project assessment.

    Skill names are sourced from:
      1. project.skills  (declared on the project)
      2. assessment.recommended_topics (LLM-extracted)
      3. assessment.strengths (LLM-extracted, filtered for skill-like tokens)

    Returns the list of updated/created UserSkill records.
    """
    raw_skills: List[str] = []

    # 1. Project skills
    if project.skills:
        raw_skills.extend(project.skills)

    # 2. Recommended topics from assessment
    if assessment.recommended_topics:
        raw_skills.extend(assessment.recommended_topics)

    # 3. Strengths that look like skill names (short phrases)
    if assessment.strengths:
        for s in assessment.strengths:
            if len(s.split()) <= 4:
                raw_skills.append(s)

    # Deduplicate & normalise
    seen: set[str] = set()
    skill_names: List[str] = []
    for raw in raw_skills:
        normalised = raw.strip().lower()
        if normalised and normalised not in seen:
            seen.add(normalised)
            skill_names.append(normalised)

    if not skill_names:
        return []

    # Fetch existing skills for this user
    existing = (
        db.query(UserSkill)
        .filter(UserSkill.user_id == user_id)
        .all()
    )
    existing_by_name: Dict[str, UserSkill] = {s.name.lower(): s for s in existing}

    updated: List[UserSkill] = []
    score = assessment.score or 0

    for name in skill_names:
        skill = existing_by_name.get(name)
        if skill:
            skill.assessment_count += 1
            skill.total_score += score
            skill.proficiency = _compute_proficiency(skill.total_score, skill.assessment_count)
            skill.domain = _classify_domain(name)
            skill.last_assessed_at = datetime.now(timezone.utc)
        else:
            skill = UserSkill(
                user_id=user_id,
                name=name,
                domain=_classify_domain(name),
                proficiency=_compute_proficiency(score, 1),
                assessment_count=1,
                total_score=score,
                last_assessed_at=datetime.now(timezone.utc),
            )
            db.add(skill)
            existing_by_name[name] = skill
        updated.append(skill)

    db.commit()
    for s in updated:
        db.refresh(s)

    logger.info(
        "Skill map updated for user=%s: %d skills touched (score=%d)",
        user_id, len(updated), score,
    )
    return updated


def get_skill_map(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Return the skill graph for a user, structured for D3.js/force-graph.

    Response shape:
    {
      "nodes": [
        {"id": "python", "domain": "Data Science", "proficiency": 0.72,
         "assessment_count": 3, "last_assessed_at": "..."}
      ],
      "edges": [
        {"source": "python", "target": "pandas", "weight": 2}
      ],
      "domains": {
        "Data Science": {"skill_count": 4, "avg_proficiency": 0.65},
        ...
      },
      "summary": {
        "total_skills": 12,
        "strongest_domain": "Web Dev",
        "strongest_skill": "react"
      }
    }
    """
    skills: List[UserSkill] = (
        db.query(UserSkill)
        .filter(UserSkill.user_id == user_id)
        .all()
    )

    if not skills:
        return {
            "nodes": [],
            "edges": [],
            "domains": {},
            "summary": {"total_skills": 0, "strongest_domain": None, "strongest_skill": None},
        }

    # ── Nodes ──
    nodes = []
    for s in skills:
        nodes.append({
            "id": s.name,
            "domain": s.domain or "General",
            "proficiency": s.proficiency,
            "assessment_count": s.assessment_count,
            "last_assessed_at": s.last_assessed_at.isoformat() if s.last_assessed_at else None,
        })

    # ── Edges (co-occurrence) ──
    # Two skills share an edge if they were both present on the same project.
    # We compute this from ProjectAssessment + Project.skills.
    assessment_rows = (
        db.query(ProjectAssessment)
        .filter(ProjectAssessment.user_id == user_id)
        .all()
    )

    skill_name_set = {s.name for s in skills}
    co_occur: Dict[tuple, int] = defaultdict(int)

    for pa in assessment_rows:
        project = db.query(Project).filter(Project.id == pa.project_id).first()
        if not project:
            continue
        project_skills = [s.strip().lower() for s in (project.skills or [])]
        # Add recommended_topics from the assessment
        if pa.recommended_topics:
            project_skills.extend([t.strip().lower() for t in pa.recommended_topics])
        # Filter to skills the user actually has
        relevant = [s for s in set(project_skills) if s in skill_name_set]
        # Build pairwise edges
        for i in range(len(relevant)):
            for j in range(i + 1, len(relevant)):
                pair = tuple(sorted([relevant[i], relevant[j]]))
                co_occur[pair] += 1

    edges = [
        {"source": pair[0], "target": pair[1], "weight": count}
        for pair, count in co_occur.items()
    ]

    # ── Domain aggregation ──
    domain_agg: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"skills": [], "total_prof": 0.0})
    for s in skills:
        d = s.domain or "General"
        domain_agg[d]["skills"].append(s.name)
        domain_agg[d]["total_prof"] += s.proficiency

    domains = {}
    for d, info in domain_agg.items():
        count = len(info["skills"])
        domains[d] = {
            "skill_count": count,
            "avg_proficiency": round(info["total_prof"] / count, 3) if count else 0,
            "skills": info["skills"],
        }

    # ── Summary ──
    strongest_skill = max(skills, key=lambda s: s.proficiency)
    strongest_domain = max(domains.items(), key=lambda kv: kv[1]["avg_proficiency"])[0] if domains else None

    return {
        "nodes": nodes,
        "edges": edges,
        "domains": domains,
        "summary": {
            "total_skills": len(skills),
            "strongest_domain": strongest_domain,
            "strongest_skill": strongest_skill.name,
        },
    }
