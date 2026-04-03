"""
Portfolio Service — generates portfolio data and AI summaries for user projects.

Fetches completed projects through the LearningPlan → Project chain,
generates professional AI summaries using OpenAI, and supports PDF export.
"""

from __future__ import annotations

import io
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import openai
from sqlalchemy.orm import Session

from ..models.learning_plan import LearningPlan
from ..models.project import Project, ProjectAssessment, ProjectPhase

logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")


def get_portfolio_projects(db: Session, user_id: str) -> List[Dict[str, Any]]:
    """
    Fetch all completed projects for a user with their assessments.

    Returns a list of project dicts suitable for the portfolio response.
    """
    # Get all learning plans for the user
    learning_plans = (
        db.query(LearningPlan)
        .filter(LearningPlan.user_id == user_id)
        .all()
    )

    plan_ids = [lp.id for lp in learning_plans]
    if not plan_ids:
        return []

    # Get completed projects across all learning plans
    projects = (
        db.query(Project)
        .filter(
            Project.learning_plan_id.in_(plan_ids),
            Project.phase == ProjectPhase.COMPLETED,
        )
        .order_by(Project.end_date.desc().nullslast(), Project.updated_at.desc())
        .all()
    )

    results = []
    for project in projects:
        # Get the best assessment for this project
        assessment = (
            db.query(ProjectAssessment)
            .filter(
                ProjectAssessment.project_id == project.id,
                ProjectAssessment.user_id == user_id,
            )
            .order_by(ProjectAssessment.assessed_at.desc())
            .first()
        )

        results.append({
            "project_id": project.id,
            "title": project.title,
            "description": project.description or "",
            "skills": project.skills or [],
            "completion_date": (
                project.end_date.isoformat() if project.end_date else
                project.updated_at.isoformat() if project.updated_at else None
            ),
            "portfolio_summary": project.portfolio_summary,
            "assessment": {
                "score": assessment.score,
                "completeness_score": assessment.completeness_score,
                "quality_score": assessment.quality_score,
                "skill_alignment_score": assessment.skill_alignment_score,
                "strengths": assessment.strengths or [],
                "feedback": assessment.feedback,
            } if assessment else None,
        })

    return results


def generate_ai_summary(project_data: Dict[str, Any]) -> str:
    """Generate a professional AI summary for a single project."""
    prompt = (
        "Write a concise, professional 1-2 paragraph portfolio summary for the "
        "following completed learning project. Highlight what was built, skills "
        "demonstrated, and the quality of work. Write in third person.\n\n"
        f"Project: {project_data['title']}\n"
        f"Description: {project_data['description']}\n"
        f"Skills used: {', '.join(project_data['skills']) if project_data['skills'] else 'N/A'}\n"
    )

    assessment = project_data.get("assessment")
    if assessment:
        prompt += (
            f"Assessment score: {assessment['score']}/100\n"
            f"Strengths: {', '.join(assessment['strengths']) if assessment['strengths'] else 'N/A'}\n"
            f"Feedback: {assessment['feedback'] or 'N/A'}\n"
        )

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional portfolio writer for a learning platform."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("AI summary generation failed for project %s: %s", project_data.get("title"), exc)
        return ""


def generate_portfolio_summaries(db: Session, user_id: str) -> List[Dict[str, Any]]:
    """
    Generate AI summaries for all completed projects that don't have one yet.
    Caches the summary on the Project row.
    """
    projects = get_portfolio_projects(db, user_id)

    for p in projects:
        if not p["portfolio_summary"]:
            summary = generate_ai_summary(p)
            if summary:
                project = db.query(Project).filter(Project.id == p["project_id"]).first()
                if project:
                    project.portfolio_summary = summary
                    p["portfolio_summary"] = summary

    db.commit()
    return projects


def generate_portfolio_pdf(db: Session, user_id: str, user_name: str) -> bytes:
    """
    Generate a PDF of the user's portfolio using reportlab.

    Returns raw PDF bytes.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    projects = get_portfolio_projects(db, user_id)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PortfolioTitle",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=20,
        textColor=colors.HexColor("#1a1a2e"),
    )
    heading_style = ParagraphStyle(
        "ProjectHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=16,
        spaceAfter=6,
        textColor=colors.HexColor("#16213e"),
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        spaceAfter=8,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["BodyText"],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=4,
    )

    elements = []
    elements.append(Paragraph(f"{user_name}'s Project Portfolio", title_style))
    elements.append(Paragraph(
        f"Generated on {datetime.utcnow().strftime('%B %d, %Y')} | {len(projects)} completed projects",
        meta_style,
    ))
    elements.append(Spacer(1, 12))

    if not projects:
        elements.append(Paragraph("No completed projects yet.", body_style))
    else:
        for p in projects:
            elements.append(Paragraph(p["title"], heading_style))

            skills_text = ", ".join(p["skills"]) if p["skills"] else "N/A"
            elements.append(Paragraph(f"<b>Skills:</b> {skills_text}", meta_style))

            if p.get("completion_date"):
                elements.append(Paragraph(f"<b>Completed:</b> {p['completion_date'][:10]}", meta_style))

            assessment = p.get("assessment")
            if assessment:
                score_data = [
                    ["Overall", "Completeness", "Quality", "Skill Alignment"],
                    [
                        str(assessment.get("score", "—")),
                        str(assessment.get("completeness_score") or "—"),
                        str(assessment.get("quality_score") or "—"),
                        str(assessment.get("skill_alignment_score") or "—"),
                    ],
                ]
                score_table = Table(score_data, colWidths=[1.2 * inch] * 4)
                score_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eaf6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdbdbd")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                elements.append(Spacer(1, 4))
                elements.append(score_table)

            summary = p.get("portfolio_summary") or p.get("description") or ""
            if summary:
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(summary, body_style))

            elements.append(Spacer(1, 12))

    doc.build(elements)
    buf.seek(0)
    return buf.read()
