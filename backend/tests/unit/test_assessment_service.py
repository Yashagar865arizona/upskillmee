"""
Unit tests for the assessment service.
Tests LLM-based scoring, fallback logic, and DB upsert behaviour.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.assessment_service import assess_project, get_assessment, _build_project_summary
from app.models.project import Project, Task, TaskSubmission, ProjectAssessment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project(task_count=3, completed_count=2):
    project = MagicMock(spec=Project)
    project.id = "proj-1"
    project.title = "Build a REST API"
    project.description = "Create a FastAPI service"
    project.skills = ["python", "fastapi"]
    project.progress_percentage = round((completed_count / task_count) * 100)

    tasks = []
    for i in range(task_count):
        t = MagicMock(spec=Task)
        t.id = f"task-{i}"
        t.title = f"Task {i}"
        t.description = f"Description {i}"
        t.completed = i < completed_count
        tasks.append(t)
    project.tasks = tasks
    return project


def _make_assessment(project_id="proj-1", user_id="user-1", score=82):
    a = MagicMock(spec=ProjectAssessment)
    a.id = "assess-1"
    a.project_id = project_id
    a.user_id = user_id
    a.score = score
    a.completeness_score = 90
    a.quality_score = 78
    a.skill_alignment_score = 80
    a.feedback = "Good work overall."
    a.strengths = ["Clean code"]
    a.improvements = ["Add more tests"]
    a.next_steps = ["Learn async"]
    a.recommended_topics = ["asyncio"]
    a.assessment_report = {"overall_score": score}
    a.assessed_at = datetime.utcnow()
    return a


# ---------------------------------------------------------------------------
# Tests: _build_project_summary
# ---------------------------------------------------------------------------

class TestBuildProjectSummary:
    def test_includes_project_title(self):
        project = _make_project()
        subs = []
        summary = _build_project_summary(project, subs)
        assert "Build a REST API" in summary

    def test_includes_skill_names(self):
        project = _make_project()
        subs = []
        summary = _build_project_summary(project, subs)
        assert "python" in summary
        assert "fastapi" in summary

    def test_marks_completed_tasks(self):
        project = _make_project(task_count=2, completed_count=1)
        subs = []
        summary = _build_project_summary(project, subs)
        assert "[completed]" in summary
        assert "[pending]" in summary

    def test_includes_submission_score(self):
        project = _make_project(task_count=1, completed_count=1)
        sub = MagicMock(spec=TaskSubmission)
        sub.task_id = "task-0"
        sub.score = "85"
        sub.feedback = "Great job!"
        summary = _build_project_summary(project, [sub])
        assert "score=85" in summary


# ---------------------------------------------------------------------------
# Tests: assess_project
# ---------------------------------------------------------------------------

class TestAssessProject:
    def _mock_db(self, project=None, existing_assessment=None):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            project,          # project lookup
            existing_assessment,  # existing assessment lookup
        ]
        return db

    def test_raises_if_project_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="not found"):
            assess_project(db, "bad-id", "user-1")

    @patch("app.services.assessment_service._call_llm")
    def test_creates_new_assessment_when_none_exists(self, mock_llm):
        mock_llm.return_value = {
            "overall_score": 75,
            "completeness_score": 80,
            "quality_score": 70,
            "skill_alignment_score": 75,
            "feedback": "Decent work.",
            "strengths": ["Good structure"],
            "improvements": ["More tests"],
            "next_steps": ["Deploy it"],
            "recommended_topics": ["docker"],
        }
        project = _make_project()
        db = MagicMock()
        # First call: project found; second call: no existing assessment
        db.query.return_value.filter.return_value.first.side_effect = [
            project, None
        ]
        db.query.return_value.filter.return_value.all.return_value = []

        result = assess_project(db, "proj-1", "user-1")

        added_types = [type(call.args[0]).__name__ for call in db.add.call_args_list]
        assert "ProjectAssessment" in added_types
        db.commit.assert_called()
        assert result.score == 75

    @patch("app.services.assessment_service._call_llm")
    def test_updates_existing_assessment(self, mock_llm):
        mock_llm.return_value = {
            "overall_score": 90,
            "completeness_score": 95,
            "quality_score": 88,
            "skill_alignment_score": 87,
            "feedback": "Excellent!",
            "strengths": ["Fast"],
            "improvements": [],
            "next_steps": ["Write more tests"],
            "recommended_topics": ["pytest"],
        }
        project = _make_project()
        existing = _make_assessment()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            project, existing
        ]
        db.query.return_value.filter.return_value.all.return_value = []

        result = assess_project(db, "proj-1", "user-1")

        added_types = [type(call.args[0]).__name__ for call in db.add.call_args_list]
        assert "ProjectAssessment" not in added_types  # upsert — no new assessment added
        assert result.score == 90

    @patch("app.services.assessment_service._call_llm", side_effect=Exception("API down"))
    def test_fallback_scoring_when_llm_fails(self, _mock_llm):
        project = _make_project(task_count=4, completed_count=3)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            project, None
        ]
        db.query.return_value.filter.return_value.all.return_value = []

        result = assess_project(db, "proj-1", "user-1")

        assert result.score == 75  # 3/4 * 100
        assert "AI evaluation temporarily unavailable" in result.feedback


# ---------------------------------------------------------------------------
# Tests: get_assessment
# ---------------------------------------------------------------------------

class TestGetAssessment:
    def test_returns_assessment_when_found(self):
        assessment = _make_assessment()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = assessment
        result = get_assessment(db, "proj-1", "user-1")
        assert result is assessment

    def test_returns_none_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = get_assessment(db, "proj-1", "user-1")
        assert result is None
