"""
Project service for handling project-related operations
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, List
import logging
from ..models.project import Project, ProjectPhase
from datetime import datetime, timedelta
from app.models.project import Task
from uuid import uuid4

logger = logging.getLogger(__name__)

class ProjectService:
    async def check_updates(self, message: str, response: str) -> Optional[Dict]:
        """Check if any project updates are needed based on the conversation"""
        try:
            # For now, return None as we'll implement the logic later
            return None
            
        except Exception as e:
            logger.error(f"Error checking project updates: {str(e)}")
            return None

    async def get_active_project(self, user_id: str) -> Optional[Dict]:
        """Get the active project for a user"""
        try:
            # For now, return None as we'll implement the logic later
            return None
        except Exception as e:
            logger.error(f"Error getting active project: {str(e)}")
            return None

    async def create_project(self, db: Session, name: str, duration_weeks: int) -> Project:
        """Create a new project with default phases"""
        try:
            project = Project(
                name=name,
                status="active",
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(weeks=duration_weeks)
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            return project
            
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            raise

    async def update_project(self, db: Session, project_id: int, updates: Dict) -> Project:
        """Update project details"""
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Project {project_id} not found")
                
            for key, value in updates.items():
                setattr(project, key, value)
                
            db.commit()
            db.refresh(project)
            return project
            
        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
            raise

    async def create_project_with_tasks(
        self,
        db: Session,
        plan_title: str,
        plan_start_date: datetime,
        duration_weeks: int,
        projects: List[Dict],
        learning_plan_id: str
    ) -> List[Project]:
        """Create multiple projects + tasks, divided across the learning plan duration"""
        try:
            plan_end_date = plan_start_date + timedelta(weeks=duration_weeks)
            num_projects = len(projects)
            if num_projects == 0:
                return []

           
            days_per_project = (plan_end_date - plan_start_date).days // num_projects
            current_start = plan_start_date
            created_projects = []

            for i, project_item in enumerate(projects):
                project_name = project_item.get("title", f"Project {i+1}")
                project_description = project_item.get("description", "")

                project_end = current_start + timedelta(days=days_per_project)
                if i == num_projects - 1:  
                    project_end = plan_end_date

                project = Project(
                    title=project_name,
                    description=project_description,
                    status="active",
                    phase=ProjectPhase.PLANNING,
                    start_date=current_start,
                    end_date=project_end,
                    learning_plan_id=learning_plan_id,
                )
                db.add(project)
                db.commit()
                db.refresh(project)

                
                tasks = project_item.get("tasks", [])
                total_tasks = len(tasks)
                for j, task_item in enumerate(tasks):
                    if isinstance(task_item, str):
                        task_title, task_description = f"Task {i+1}.{j+1}", task_item
                    else:
                        task_title = task_item.get("title", f"Task {i+1}.{j+1}")
                        task_description = task_item.get("description", "")

                    due_date = None
                    if total_tasks > 0:
                        project_duration = (project_end - current_start).total_seconds()
                        seconds_per_task = project_duration / total_tasks
                        due_date = current_start + timedelta(seconds=seconds_per_task * (j + 1))

                    task = Task(
                        project_id=project.id,
                        title=task_title,
                        description=task_description,
                        status="pending",
                        priority="medium",
                        due_date=due_date,
                    )
                    db.add(task)
                    db.commit()

                created_projects.append(project)
                current_start = project_end + timedelta(days=1)  

            return created_projects

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating projects from plan: {str(e)}")
            raise