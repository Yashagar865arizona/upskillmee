"""
Learning Service - Manages learning plans and user progress
Simplified service focused on database operations and plan management
"""

import json
from typing import Dict, List, Any, Optional
import logging
from fastapi import HTTPException
from sqlalchemy import select
from ..database.session import AsyncSessionLocal
from app.services import project_service
from uuid import uuid4
import uuid
from app.services.project_service import ProjectService
from ..models.learning_plan import LearningPlan
from datetime import datetime

logger = logging.getLogger(__name__)

class LearningService:
    """Service for managing learning plans and user progress - database operations only."""

    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key
        self.project_service = ProjectService()

    async def get_user_plans(self, user_id: str) -> List[Dict]:
        """Get the most recent/active learning plan for a user from the database."""
        try:
            # Create async session
            async with AsyncSessionLocal() as session:
                from ..models.learning_plan import LearningPlan
                result = await session.execute(
                    select(LearningPlan)
                    .where(LearningPlan.user_id == user_id)
                    .order_by(LearningPlan.created_at.desc())
                    .limit(1)  # Only get the most recent plan
                )
                learning_plan = result.scalar_one_or_none()

                if not learning_plan:
                    logger.info(f"No learning plans found for user {user_id}")
                    return []

                # Convert to dictionary format
                plan_dict = {
                    "id": learning_plan.id,
                    "title": learning_plan.title,
                    "description": learning_plan.description,
                    "content": learning_plan.content,
                    "created_at": str(learning_plan.created_at) if learning_plan.created_at is not None else None
                }

                logger.info(f"Retrieved current learning plan for user {user_id}: {plan_dict['title']}")
                return [plan_dict]  
        except Exception as e:
            logger.error(f"Error retrieving learning plan for user {user_id}: {str(e)}")
            # Return empty list on error
            return []

    async def assign_ids_to_projects(plan_content: dict):
        for project in plan_content.get("projects", []):
            project["id"] = str(uuid.uuid4())
        for i, task in enumerate(project.get("tasks", [])):
            if isinstance(task, dict):
                task["id"] = str(uuid.uuid4())
            else:
                project["tasks"][i] = {"id": str(uuid.uuid4()), "description": task}
        return plan_content

  
    async def save_plan(self, plan: Dict) -> Dict:
     if "title" not in plan or "user_id" not in plan:
        raise HTTPException(status_code=400, detail="Missing required fields: title, user_id")

     async with AsyncSessionLocal() as session:
        project_service = ProjectService()

        plan_start_date = datetime.fromisoformat(plan.get("start_date")) if plan.get("start_date") else datetime.now()
        duration_weeks = plan.get("duration_weeks", 4)

        
        created_projects = await project_service.create_project_with_tasks(
            db=session.sync_session,
            plan_title=plan["title"],
            plan_start_date=plan_start_date,
            duration_weeks=duration_weeks,
            projects=plan.get("projects", []),
            learning_plan_id=str(uuid.uuid4()) 
        )

        
        learning_plan = LearningPlan(
            user_id=plan["user_id"],
            title=plan["title"],
            description=plan.get("description", ""),
            content={
                "duration_weeks": duration_weeks,
                "projects": [
                    {
                        "id": project.id,
                        "title": project.title,
                        "start_date": str(project.start_date),
                        "end_date": str(project.end_date),
                        "tasks": [
                            {
                                "id": task.id,
                                "title": task.title,
                                "description": task.description,
                                "due_date": str(task.due_date) if task.due_date else None
                            }
                            for task in project.tasks
                        ]
                    }
                    for project in created_projects
                ]
            }
        )
        session.add(learning_plan)
        await session.commit()
        await session.refresh(learning_plan)

        return learning_plan.to_dict()



    async def save_feedback(self, feedback: Dict) -> bool:
        """Save feedback for a learning plan."""
        try:
            # Save feedback to database
            from ..models.feedback import Feedback
            
            feedback_record = Feedback(
                user_id=feedback.get('user_id'),
                plan_id=feedback['plan_id'],
                rating=5 if feedback['is_positive'] else 2,
                comment=feedback.get('comment', ''),
                feedback_type='plan_rating'
            )
            
            self.db.add(feedback_record)
            self.db.commit()
            
            logger.info(f"Saved feedback for plan {feedback['plan_id']}: {feedback['is_positive']}")
            return True
        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"Missing required field: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
            raise HTTPException(status_code=500, detail="Failed to save feedback")

    async def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's learning progress."""
        try:
            # Get actual progress from database
            from ..models import UserProject, Conversation
            from sqlalchemy import func
            
            # Count completed and active projects
            completed_projects = self.db.query(UserProject).filter(
                UserProject.user_id == str(user_id),
                UserProject.status == 'completed'
            ).count()
            
            active_projects = self.db.query(UserProject).filter(
                UserProject.user_id == str(user_id),
                UserProject.status == 'active'
            ).count()
            
            # Estimate total hours from conversation count (rough estimate)
            conversation_count = self.db.query(Conversation).filter(
                Conversation.user_id == str(user_id)
            ).count()
            estimated_hours = conversation_count * 0.5  # Rough estimate
            
            return {
                "completed_projects": completed_projects,
                "active_projects": active_projects,
                "total_hours": int(estimated_hours),
                "achievements": []  # Could be implemented later
            }
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get user progress")

    async def update_progress(self, user_id: str, progress_data: Dict[str, Any]) -> bool:
        """Update user's learning progress."""
        try:
            # Update progress in database
            from ..models import UserProject
            
            project_id = progress_data.get('project_id')
            if project_id:
                project = self.db.query(UserProject).filter(
                    UserProject.id == project_id,
                    UserProject.user_id == str(user_id)
                ).first()
                
                if project:
                    # Update project status if provided
                    if 'status' in progress_data:
                        project.status = progress_data['status']
                    
                    # Update progress percentage if provided
                    if 'progress_percentage' in progress_data:
                        project.progress_percentage = progress_data['progress_percentage']
                    
                    self.db.commit()
                    logger.info(f"Updated progress for user {user_id}, project {project_id}")
                    return True
            
            logger.warning(f"No valid project found for progress update: {progress_data}")
            return False
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update progress")