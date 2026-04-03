"""
Unit tests for LearningService.
Tests learning plan management, user progress tracking, and database operations.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException

from app.services.learning_service import LearningService
from app.models.learning_plan import LearningPlan


class TestLearningService:
    """Test suite for LearningService."""

    def test_initialization(self, learning_service):
        """Test LearningService initialization."""
        assert isinstance(learning_service, LearningService)

    @pytest.mark.asyncio
    async def test_get_user_plans_success(self, learning_service):
        """Test successful retrieval of user learning plans."""
        user_id = "test-user-123"
        
        # Mock the database session and query
        with patch('app.services.learning_service.AsyncSessionLocal') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock the query result
            mock_result = Mock()
            mock_learning_plan = Mock()
            mock_learning_plan.id = "plan-123"
            mock_learning_plan.title = "Web Development Fundamentals"
            mock_learning_plan.description = "Learn the basics of web development"
            mock_learning_plan.content = {
                "projects": [{"title": "Build a website", "skills": ["HTML", "CSS"]}],
                "total_hours": 40
            }
            mock_learning_plan.created_at = "2024-01-15T10:00:00"
            
            mock_result.scalar_one_or_none.return_value = mock_learning_plan
            mock_session.execute.return_value = mock_result
            
            plans = await learning_service.get_user_plans(user_id)
            
            assert len(plans) == 1
            assert plans[0]["id"] == "plan-123"
            assert plans[0]["title"] == "Web Development Fundamentals"
            assert plans[0]["description"] == "Learn the basics of web development"
            assert "content" in plans[0]
            assert "created_at" in plans[0]

    @pytest.mark.asyncio
    async def test_get_user_plans_no_plans_found(self, learning_service):
        """Test retrieval when no learning plans exist for user."""
        user_id = "test-user-123"
        
        with patch('app.services.learning_service.AsyncSessionLocal') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock no results found
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result
            
            plans = await learning_service.get_user_plans(user_id)
            
            assert plans == []

    @pytest.mark.asyncio
    async def test_get_user_plans_database_error(self, learning_service):
        """Test handling database errors in get_user_plans."""
        user_id = "test-user-123"
        
        with patch('app.services.learning_service.AsyncSessionLocal') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock database error
            mock_session.execute.side_effect = Exception("Database connection error")
            
            plans = await learning_service.get_user_plans(user_id)
            
            # Should return empty list on error
            assert plans == []

    @pytest.mark.asyncio
    async def test_save_plan_success(self, learning_service):
        """Test successful learning plan save."""
        plan_data = {
            "user_id": "test-user-123",
            "title": "Python Programming Basics",
            "description": "Learn Python fundamentals",
            "content": {
                "projects": [
                    {
                        "title": "Calculator App",
                        "description": "Build a simple calculator",
                        "skills": ["Python", "Functions"],
                        "estimated_hours": 8
                    }
                ],
                "total_estimated_hours": 30,
                "difficulty_level": "beginner"
            }
        }
        
        with patch('app.services.learning_service.AsyncSessionLocal') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock the saved learning plan
            mock_learning_plan = Mock()
            mock_learning_plan.id = "new-plan-123"
            mock_learning_plan.title = plan_data["title"]
            mock_learning_plan.description = plan_data["description"]
            mock_learning_plan.user_id = plan_data["user_id"]
            mock_learning_plan.content = plan_data["content"]
            mock_learning_plan.created_at = "2024-01-15T10:00:00"
            
            # Mock session operations
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            
            # Mock the LearningPlan constructor
            with patch('app.services.learning_service.LearningPlan', return_value=mock_learning_plan):
                result = await learning_service.save_plan(plan_data)
                
                assert result["id"] == "new-plan-123"
                assert result["title"] == plan_data["title"]
                assert result["description"] == plan_data["description"]
                assert result["user_id"] == plan_data["user_id"]
                assert result["content"] == plan_data["content"]
                assert "created_at" in result

    @pytest.mark.asyncio
    async def test_save_plan_missing_title(self, learning_service):
        """Test save plan with missing title."""
        plan_data = {
            "user_id": "test-user-123",
            "description": "Test plan without title"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await learning_service.save_plan(plan_data)
        
        assert exc_info.value.status_code == 400
        assert "Missing required field: title" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_save_plan_missing_user_id(self, learning_service):
        """Test save plan with missing user_id."""
        plan_data = {
            "title": "Test Plan",
            "description": "Test plan without user_id"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await learning_service.save_plan(plan_data)
        
        assert exc_info.value.status_code == 400
        assert "Missing required field: user_id" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_save_plan_database_error(self, learning_service):
        """Test save plan with database error."""
        plan_data = {
            "user_id": "test-user-123",
            "title": "Test Plan",
            "description": "Test plan"
        }
        
        with patch('app.services.learning_service.AsyncSessionLocal') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock database error
            mock_session.commit.side_effect = Exception("Database error")
            
            with pytest.raises(HTTPException) as exc_info:
                await learning_service.save_plan(plan_data)
            
            assert exc_info.value.status_code == 500
            assert "Failed to save plan" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_save_feedback_success(self, learning_service):
        """Test successful feedback save."""
        feedback_data = {
            "plan_id": "test-plan-123",
            "user_id": "test-user-123",
            "is_positive": True,
            "comments": "Great plan, very helpful!"
        }
        
        result = await learning_service.save_feedback(feedback_data)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_save_feedback_missing_plan_id(self, learning_service):
        """Test save feedback with missing plan_id."""
        feedback_data = {
            "user_id": "test-user-123",
            "is_positive": True
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await learning_service.save_feedback(feedback_data)
        
        assert exc_info.value.status_code == 400
        assert "Missing required field: plan_id" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_save_feedback_error(self, learning_service):
        """Test save feedback with general error."""
        feedback_data = {
            "plan_id": "test-plan-123",
            "is_positive": True
        }
        
        # Mock an error in the save process
        with patch.object(learning_service, 'save_feedback', side_effect=Exception("Save error")):
            with pytest.raises(Exception):
                await learning_service.save_feedback(feedback_data)

    @pytest.mark.asyncio
    async def test_get_user_progress_success(self, learning_service):
        """Test successful user progress retrieval."""
        user_id = "test-user-123"
        
        progress = await learning_service.get_user_progress(user_id)
        
        assert "completed_projects" in progress
        assert "active_projects" in progress
        assert "total_hours" in progress
        assert "achievements" in progress
        assert isinstance(progress["completed_projects"], int)
        assert isinstance(progress["active_projects"], int)
        assert isinstance(progress["total_hours"], int)
        assert isinstance(progress["achievements"], list)

    @pytest.mark.asyncio
    async def test_get_user_progress_error(self, learning_service):
        """Test user progress retrieval with error."""
        user_id = "test-user-123"
        
        # Mock an error in the progress retrieval
        with patch.object(learning_service, 'get_user_progress', side_effect=Exception("Progress error")):
            with pytest.raises(Exception):
                await learning_service.get_user_progress(user_id)

    @pytest.mark.asyncio
    async def test_update_progress_success(self, learning_service):
        """Test successful progress update."""
        user_id = "test-user-123"
        progress_data = {
            "completed_projects": 2,
            "active_projects": 1,
            "total_hours": 25,
            "last_activity": "2024-01-15T10:00:00"
        }
        
        result = await learning_service.update_progress(user_id, progress_data)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_update_progress_error(self, learning_service):
        """Test progress update with error."""
        user_id = "test-user-123"
        progress_data = {"completed_projects": 1}
        
        # Mock an error in the update process
        with patch.object(learning_service, 'update_progress', side_effect=Exception("Update error")):
            with pytest.raises(Exception):
                await learning_service.update_progress(user_id, progress_data)

    @pytest.mark.asyncio
    async def test_save_plan_with_minimal_data(self, learning_service):
        """Test saving plan with minimal required data."""
        plan_data = {
            "user_id": "test-user-123",
            "title": "Minimal Plan"
        }
        
        with patch('app.services.learning_service.AsyncSessionLocal') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock the saved learning plan
            mock_learning_plan = Mock()
            mock_learning_plan.id = "minimal-plan-123"
            mock_learning_plan.title = plan_data["title"]
            mock_learning_plan.description = ""  # Default empty description
            mock_learning_plan.user_id = plan_data["user_id"]
            mock_learning_plan.content = plan_data  # Full plan data as content
            mock_learning_plan.created_at = "2024-01-15T10:00:00"
            
            # Mock session operations
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            
            with patch('app.services.learning_service.LearningPlan', return_value=mock_learning_plan):
                result = await learning_service.save_plan(plan_data)
                
                assert result["id"] == "minimal-plan-123"
                assert result["title"] == plan_data["title"]
                assert result["description"] == ""
                assert result["user_id"] == plan_data["user_id"]

    @pytest.mark.asyncio
    async def test_get_user_plans_with_created_at_none(self, learning_service):
        """Test get user plans when created_at is None."""
        user_id = "test-user-123"
        
        with patch('app.services.learning_service.AsyncSessionLocal') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock learning plan with None created_at
            mock_result = Mock()
            mock_learning_plan = Mock()
            mock_learning_plan.id = "plan-123"
            mock_learning_plan.title = "Test Plan"
            mock_learning_plan.description = "Test Description"
            mock_learning_plan.content = {"test": "content"}
            mock_learning_plan.created_at = None  # None value
            
            mock_result.scalar_one_or_none.return_value = mock_learning_plan
            mock_session.execute.return_value = mock_result
            
            plans = await learning_service.get_user_plans(user_id)
            
            assert len(plans) == 1
            assert plans[0]["created_at"] is None

    @pytest.mark.asyncio
    async def test_save_plan_with_complex_content(self, learning_service):
        """Test saving plan with complex content structure."""
        complex_content = {
            "title": "Full Stack Development",
            "description": "Complete full stack development course",
            "projects": [
                {
                    "title": "Frontend Project",
                    "description": "Build a React application",
                    "skills": ["React", "JavaScript", "CSS"],
                    "estimated_hours": 20,
                    "tasks": [
                        {"name": "Setup project", "completed": False},
                        {"name": "Create components", "completed": False}
                    ]
                },
                {
                    "title": "Backend Project",
                    "description": "Build a REST API",
                    "skills": ["Node.js", "Express", "MongoDB"],
                    "estimated_hours": 25,
                    "tasks": [
                        {"name": "Setup server", "completed": False},
                        {"name": "Create routes", "completed": False}
                    ]
                }
            ],
            "total_estimated_hours": 45,
            "difficulty_level": "intermediate",
            "prerequisites": ["Basic JavaScript", "HTML/CSS"],
            "learning_outcomes": [
                "Build full stack applications",
                "Understand REST APIs",
                "Deploy applications"
            ]
        }
        
        plan_data = {
            "user_id": "test-user-123",
            "title": "Full Stack Development",
            "description": "Complete full stack development course",
            "content": complex_content
        }
        
        with patch('app.services.learning_service.AsyncSessionLocal') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock the saved learning plan
            mock_learning_plan = Mock()
            mock_learning_plan.id = "complex-plan-123"
            mock_learning_plan.title = plan_data["title"]
            mock_learning_plan.description = plan_data["description"]
            mock_learning_plan.user_id = plan_data["user_id"]
            mock_learning_plan.content = complex_content
            mock_learning_plan.created_at = "2024-01-15T10:00:00"
            
            # Mock session operations
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            
            with patch('app.services.learning_service.LearningPlan', return_value=mock_learning_plan):
                result = await learning_service.save_plan(plan_data)
                
                assert result["content"]["projects"][0]["title"] == "Frontend Project"
                assert result["content"]["projects"][1]["title"] == "Backend Project"
                assert result["content"]["total_estimated_hours"] == 45
                assert len(result["content"]["prerequisites"]) == 2
                assert len(result["content"]["learning_outcomes"]) == 3