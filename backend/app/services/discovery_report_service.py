"""
Discovery Report Service — generates self-discovery reports for users.

After a user completes 3+ assessed projects, this service aggregates data from
UserInterestProfile, ProjectAssessment, PostProjectDiscovery, and Project to
build a structured report with four sections:

  1. Interest patterns (domain weights, learning style)
  2. Strength signals (high-scoring domains, assessment-derived strengths)
  3. Domains explored (breadth of projects tackled)
  4. Pivot suggestions (new directions based on interest graph)

Reports are cached in the discovery_reports table and invalidated when the
assessed project count changes.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import openai
from sqlalchemy.orm import Session

from ..models.learning_plan import LearningPlan
from ..models.project import (
    DiscoveryReport,
    PostProjectDiscovery,
    Project,
    ProjectAssessment,
    ProjectPhase,
)
from ..models.user import User, UserInterestProfile, UserProfile

logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

MIN_ASSESSED_PROJECTS = 3


def _generate_share_token() -> str:
    """Generate a URL-safe share token."""
    return secrets.token_urlsafe(24)


def _count_assessed_projects(db: Session, user_id: str) -> int:
    """Count distinct projects that have at least one assessment for this user."""
    return (
        db.query(ProjectAssessment.project_id)
        .filter(ProjectAssessment.user_id == user_id)
        .distinct()
        .count()
    )


def _get_assessed_projects_data(
    db: Session, user_id: str
) -> List[Dict[str, Any]]:
    """Fetch projects with their assessments and discoveries for the user."""
    # Get all assessments for this user
    assessments = (
        db.query(ProjectAssessment)
        .filter(ProjectAssessment.user_id == user_id)
        .order_by(ProjectAssessment.assessed_at.desc())
        .all()
    )

    results = []
    for assessment in assessments:
        project = db.query(Project).filter(Project.id == assessment.project_id).first()
        if not project:
            continue

        discovery = (
            db.query(PostProjectDiscovery)
            .filter(
                PostProjectDiscovery.project_id == project.id,
                PostProjectDiscovery.user_id == user_id,
            )
            .first()
        )

        results.append({
            "project_title": project.title,
            "project_description": project.description or "",
            "project_skills": project.skills or [],
            "score": assessment.score,
            "completeness_score": assessment.completeness_score,
            "quality_score": assessment.quality_score,
            "skill_alignment_score": assessment.skill_alignment_score,
            "strengths": assessment.strengths or [],
            "improvements": assessment.improvements or [],
            "recommended_topics": assessment.recommended_topics or [],
            "feedback": assessment.feedback or "",
            "discovery": {
                "enjoyed_aspects": discovery.enjoyed_aspects if discovery else None,
                "struggled_aspects": discovery.struggled_aspects if discovery else None,
                "would_continue": discovery.would_continue if discovery else None,
                "engagement_score": discovery.engagement_score if discovery else None,
                "domains_confirmed": discovery.domains_confirmed if discovery else [],
                "domains_rejected": discovery.domains_rejected if discovery else [],
            } if discovery else None,
        })

    return results


def _build_interest_patterns(
    interest_profile: Optional[Dict], projects_data: List[Dict]
) -> Dict[str, Any]:
    """Build the interest patterns section from interest profile and project data."""
    domains = {}
    if interest_profile:
        domains = interest_profile.get("domains", {})

    # Enrich with discovery data
    for p in projects_data:
        disc = p.get("discovery")
        if disc:
            for domain in disc.get("domains_confirmed", []):
                d = str(domain).lower().strip()
                if d and d not in domains:
                    domains[d] = 0.7

    # Sort by weight descending
    sorted_domains = dict(
        sorted(domains.items(), key=lambda x: x[1], reverse=True)
    )

    return {
        "domains": sorted_domains,
        "learning_style": interest_profile.get("learning_style") if interest_profile else None,
        "aversions": interest_profile.get("aversions", []) if interest_profile else [],
        "confidence_level": interest_profile.get("confidence_level", 0.0) if interest_profile else 0.0,
    }


def _build_strength_signals(
    interest_profile: Optional[Dict], projects_data: List[Dict]
) -> Dict[str, Any]:
    """Build strength signals from assessment scores and interest profile."""
    # Collect all strengths from assessments
    all_strengths: List[str] = []
    if interest_profile:
        all_strengths.extend(interest_profile.get("strengths", []))

    for p in projects_data:
        all_strengths.extend(p.get("strengths", []))

    # Deduplicate
    seen = set()
    unique_strengths = []
    for s in all_strengths:
        key = s.lower().strip()
        if key not in seen:
            seen.add(key)
            unique_strengths.append(s)

    # High-scoring domains (projects with score >= 70)
    high_scoring_domains: List[Dict] = []
    for p in projects_data:
        if p["score"] >= 70:
            high_scoring_domains.append({
                "project": p["project_title"],
                "score": p["score"],
                "skills": p["project_skills"],
            })

    # Average scores across dimensions
    scores = [p["score"] for p in projects_data]
    completeness = [p["completeness_score"] for p in projects_data if p["completeness_score"]]
    quality = [p["quality_score"] for p in projects_data if p["quality_score"]]

    return {
        "strengths": unique_strengths[:15],
        "high_scoring_domains": high_scoring_domains,
        "average_score": round(sum(scores) / len(scores)) if scores else 0,
        "average_completeness": round(sum(completeness) / len(completeness)) if completeness else 0,
        "average_quality": round(sum(quality) / len(quality)) if quality else 0,
        "total_projects_assessed": len(projects_data),
    }


def _build_domains_explored(projects_data: List[Dict]) -> Dict[str, Any]:
    """Build a breadth visualization of domains explored."""
    domain_map: Dict[str, Dict] = {}

    for p in projects_data:
        for skill in p["project_skills"]:
            key = skill.lower().strip()
            if key not in domain_map:
                domain_map[key] = {
                    "name": skill,
                    "project_count": 0,
                    "best_score": 0,
                    "projects": [],
                }
            domain_map[key]["project_count"] += 1
            domain_map[key]["best_score"] = max(
                domain_map[key]["best_score"], p["score"]
            )
            domain_map[key]["projects"].append(p["project_title"])

    # Sort by project count then score
    sorted_domains = sorted(
        domain_map.values(),
        key=lambda x: (x["project_count"], x["best_score"]),
        reverse=True,
    )

    return {
        "domains": sorted_domains,
        "total_unique_skills": len(domain_map),
        "total_projects": len(projects_data),
    }


def _build_pivot_suggestions(
    interest_profile: Optional[Dict], projects_data: List[Dict]
) -> Dict[str, Any]:
    """Build pivot suggestions based on interest graph and recommendations."""
    # Collect all recommended topics
    all_recommendations: List[str] = []
    for p in projects_data:
        all_recommendations.extend(p.get("recommended_topics", []))

    # Deduplicate
    seen = set()
    unique_recs = []
    for r in all_recommendations:
        key = r.lower().strip()
        if key not in seen:
            seen.add(key)
            unique_recs.append(r)

    # Identify domains with medium confidence (exploration candidates)
    exploration_candidates = []
    if interest_profile:
        domains = interest_profile.get("domains", {})
        for domain, weight in domains.items():
            if 0.3 <= weight <= 0.6:
                exploration_candidates.append(domain)

    return {
        "recommended_topics": unique_recs[:10],
        "exploration_candidates": exploration_candidates[:5],
    }


def _generate_narrative(
    interest_patterns: Dict,
    strength_signals: Dict,
    domains_explored: Dict,
    pivot_suggestions: Dict,
) -> str:
    """Use OpenAI to generate a narrative summary of the report."""
    prompt = f"""You are a supportive learning coach writing a brief self-discovery summary for a student.

Based on this data, write a 3-4 paragraph narrative (max 300 words) that:
1. Highlights their strongest interest patterns and learning style
2. Celebrates their strengths and high-performing areas
3. Notes the breadth of domains they've explored
4. Suggests exciting new directions they might enjoy

Data:
- Top interest domains: {json.dumps(dict(list(interest_patterns.get('domains', {}).items())[:5]))}
- Learning style: {interest_patterns.get('learning_style', 'not yet determined')}
- Key strengths: {json.dumps(strength_signals.get('strengths', [])[:5])}
- Average score: {strength_signals.get('average_score', 0)}/100
- Projects assessed: {strength_signals.get('total_projects_assessed', 0)}
- Unique skills explored: {domains_explored.get('total_unique_skills', 0)}
- Suggested pivots: {json.dumps(pivot_suggestions.get('recommended_topics', [])[:5])}

Write in second person ("you"), be warm and encouraging but honest. No markdown headers.
Respond with ONLY the narrative text."""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("Narrative generation failed: %s", exc)
        return "Your learning journey is progressing well. Check the detailed sections below for insights into your interests, strengths, and potential new directions."


def generate_report(db: Session, user_id: str) -> DiscoveryReport:
    """
    Generate or return a cached self-discovery report.

    Raises ValueError if user has fewer than MIN_ASSESSED_PROJECTS assessed projects.
    Returns a cached report if project count hasn't changed since last generation.
    """
    assessed_count = _count_assessed_projects(db, user_id)
    if assessed_count < MIN_ASSESSED_PROJECTS:
        raise ValueError(
            f"Need at least {MIN_ASSESSED_PROJECTS} assessed projects "
            f"(currently have {assessed_count})"
        )

    # Check for cached report
    existing = (
        db.query(DiscoveryReport)
        .filter(DiscoveryReport.user_id == user_id)
        .first()
    )
    if existing and existing.project_count_at_generation == assessed_count:
        return existing

    # Gather data
    projects_data = _get_assessed_projects_data(db, user_id)

    # Get interest profile
    user_profile = (
        db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    )
    interest_profile_model = None
    if user_profile:
        interest_profile_model = (
            db.query(UserInterestProfile)
            .filter(UserInterestProfile.user_profile_id == user_profile.id)
            .first()
        )
    interest_profile = None
    if interest_profile_model:
        interest_profile = {
            "domains": interest_profile_model.domains or {},
            "strengths": interest_profile_model.strengths or [],
            "aversions": interest_profile_model.aversions or [],
            "learning_style": interest_profile_model.learning_style,
            "confidence_level": interest_profile_model.confidence_level or 0.0,
        }

    # Build report sections
    interest_patterns = _build_interest_patterns(interest_profile, projects_data)
    strength_signals = _build_strength_signals(interest_profile, projects_data)
    domains_explored = _build_domains_explored(projects_data)
    pivot_suggestions = _build_pivot_suggestions(interest_profile, projects_data)

    # Generate narrative
    narrative = _generate_narrative(
        interest_patterns, strength_signals, domains_explored, pivot_suggestions
    )

    # Upsert report
    if existing:
        report = existing
    else:
        report = DiscoveryReport(
            user_id=user_id,
            share_token=_generate_share_token(),
        )
        db.add(report)

    report.interest_patterns = interest_patterns
    report.strength_signals = strength_signals
    report.domains_explored = domains_explored
    report.pivot_suggestions = pivot_suggestions
    report.narrative_summary = narrative
    report.project_count_at_generation = assessed_count
    report.generated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(report)
    return report


def get_report_by_token(db: Session, share_token: str) -> Optional[DiscoveryReport]:
    """Fetch a report by its public share token."""
    return (
        db.query(DiscoveryReport)
        .filter(DiscoveryReport.share_token == share_token)
        .first()
    )


def get_report_by_user(db: Session, user_id: str) -> Optional[DiscoveryReport]:
    """Fetch the cached report for a user (if it exists)."""
    return (
        db.query(DiscoveryReport)
        .filter(DiscoveryReport.user_id == user_id)
        .first()
    )


def invalidate_report(db: Session, user_id: str) -> None:
    """
    Force-invalidate a user's cached report so it regenerates on next request.

    Called when a new project is completed and assessed.
    """
    existing = (
        db.query(DiscoveryReport)
        .filter(DiscoveryReport.user_id == user_id)
        .first()
    )
    if existing:
        # Set project_count to 0 so the next generate_report call will rebuild
        existing.project_count_at_generation = 0
        db.commit()
