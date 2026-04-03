"""
Location: upskillmee/backend/app/routers/learning_router.py

This module implements the learning functionality for the FastAPI backend.
Key features:
- Handles learning plan creation and retrieval
- Manages learning progress tracking
- Provides analytics and metrics endpoints
- Offers mentor profile functionality
"""

import re
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, File, UploadFile, Form,Body
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime,timedelta, timezone
import logging
from pydantic import BaseModel
from ..database import get_db
from ..config import settings
from ..services.learning_service import LearningService
from ..monitoring.metrics import ai_metrics
from app.services.evaluation_service import evaluate_submission
import json
from uuid import uuid4
from ..models.learning_plan import LearningPlan
from ..models.project import Project, Task, TaskSubmission, TaskSubmissionStatus
from sqlalchemy.future import select
from app.database.session import AsyncSessionLocal
from dateutil.parser import parse
from app.models.user import User
from app.routers.user_router import get_current_user_dependency
logger = logging.getLogger(__name__)

# Request/Response Schema Models
class LearningProgressCreate(BaseModel):
    user_id: str
    topic_id: str
    status: str
    completion_percentage: float
    time_spent_minutes: int
    notes: Optional[str] = None

class LearningProgressUpdate(BaseModel):
    status: Optional[str] = None
    completion_percentage: Optional[float] = None
    time_spent_minutes: Optional[int] = None
    notes: Optional[str] = None

class LearningSessionCreate(BaseModel):
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    topics: List[str]
    learning_goals: Optional[List[str]] = None
    achievements: Optional[List[str]] = None

def get_learning_service(db: Session = Depends(get_db)) -> LearningService:
    """Get instance of LearningService with proper configuration."""
    return LearningService(
        openai_api_key=settings.OPENAI_API_KEY
    )

# Create a class-based router for backward compatibility
class LearningRouter:
    def __init__(self):
        self.router = APIRouter()
        self._setup_routes()
        
    def _setup_routes(self):
        # Register all routes on the router
        self.router.add_api_route("/plan", self.create_learning_plan, methods=["POST"])
        self.router.add_api_route("/plans/{user_id}", self.get_learning_plans, methods=["GET"])
        self.router.add_api_route("/feedback/{plan_id}", self.save_plan_feedback, methods=["POST"])
        self.router.add_api_route("/plan/save", self.save_learning_plan, methods=["POST"])
        self.router.add_api_route("/progress", self.create_learning_progress, methods=["POST"])
        self.router.add_api_route("/progress/{progress_id}", self.update_learning_progress, methods=["PUT"])
        self.router.add_api_route("/session", self.create_learning_session, methods=["POST"])
        self.router.add_api_route("/progress/{user_id}", self.get_user_learning_progress, methods=["GET"])
        self.router.add_api_route("/analytics/{user_id}", self.get_learning_analytics, methods=["GET"])
        self.router.add_api_route("/metrics/{user_id}", self.get_learning_metrics, methods=["GET"])
        self.router.add_api_route("/mentor/profile-questions", self.get_mentor_questions, methods=["GET"])
        self.router.add_api_route("/tasks/{task_id}/submit", self.submit_task, methods=["POST"])
        # self.router.add_api_route("/tasks/{task_id}/toggle-completion", self.toggle_task_completion, methods=["POST"])


    async def create_learning_plan(
        self,
        user_profile: Dict,
        background_tasks: BackgroundTasks,
        learning_service: LearningService = Depends(get_learning_service)
    ) -> Dict:
        """Create a new learning plan based on user profile."""
        try:
            plan = await learning_service.create_learning_plan(user_profile)
            return {"status": "success", "data": plan}
        except Exception as e:
            logger.error(f"Error creating learning plan: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    

    def calculate_task_score(self, task: Task) -> int:
     if not task.completed:
        return 0
     if task.due_date and task.completed_at:
        return 100 if task.completed_at <= task.due_date else 50
     return 100

    def calculate_task_deadline(self, start_date: datetime, end_date: datetime, task_index: int, total_tasks: int) -> datetime:
     """
     Distributes tasks evenly between start_date and end_date.
     """
     if not start_date or not end_date or total_tasks <= 0:
        return None

     total_days = (end_date - start_date).days
     if total_days <= 0:
        return start_date

     days_per_task = total_days / total_tasks
     task_deadline = start_date + timedelta(days=days_per_task * (task_index + 1))
     return task_deadline
    
    def calculate_task_priority(self, task_deadline: datetime, today: datetime = None) -> str:
     """
     Sets priority based on how close the deadline is.
     """
     if not today:
        today = datetime.now(timezone.utc)

     if task_deadline and task_deadline.tzinfo is None:
        task_deadline = task_deadline.replace(tzinfo=timezone.utc)

     if not task_deadline:
        return "medium"

     days_left = (task_deadline - today).days
     if days_left <= 1:
        return "high"
     elif days_left <= 3:
        return "medium"
     else:
        return "low"

    def parse_weeks_string(self, weeks_str: str):
     """
     Converts a string like "Week 1-2" to number of weeks.
     Returns (start_week, end_week)
     """
     if not weeks_str:
        return 1, 1
     match = re.findall(r'\d+', weeks_str)
     if len(match) == 2:
        return int(match[0]), int(match[1])
     elif len(match) == 1:
        return int(match[0]), int(match[0])
     return 1, 1

    def determine_project_status(self, db_project: Project) -> str:
     """Determine if a project is active or inactive based on dates and completion."""
     now = datetime.now(timezone.utc)
     if db_project.end_date and now > db_project.end_date:
        return "inactive"
     elif db_project.start_date and now < db_project.start_date:
        return "inactive"
     elif db_project.status == "completed":
        return "inactive"
     return "active"


    async def get_learning_plans(
    self,
    user_id: str,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
     """
     Get all learning plans for a user and enrich projects and tasks.
     Features:
        - Dynamically calculates project and task phases
        - Ensures timezone-aware datetimes
        - Calculates task deadlines and priorities
        - Avoids duplicate tasks based on title + description
        - Returns JSON-safe output
     """
     try:
        plans = db.query(LearningPlan).filter(
            LearningPlan.user_id == user_id
        ).order_by(LearningPlan.created_at.desc()).all()

        plan_list = []

        for plan in plans:
            content = plan.content
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except Exception as e:
                    logger.error(f"Failed to parse plan.content for plan {plan.id}: {e}")
                    content = {}

            plan_dict = {
                "id": plan.id,
                "user_id": plan.user_id,
                "title": plan.title,
                "description": plan.description,
                "content": content,
                "created_at": plan.created_at.isoformat(),
                "updated_at": plan.updated_at.isoformat()
            }

            for project_item in plan_dict["content"].get("projects", []):
                project_title = project_item.get("title", "Untitled Project")

                
                db_project = db.query(Project).filter(
                    Project.title == project_title,
                    Project.learning_plan_id == plan.id
                ).first()

                if not db_project:
                    deadline_dt = None
                    deadline_str = project_item.get("deadline")
                    if deadline_str:
                        try:
                            deadline_dt = datetime.fromisoformat(deadline_str).replace(tzinfo=timezone.utc)
                        except Exception:
                            deadline_dt = None

                    # Safe conversion of weeks
                    weeks_value = project_item.get("weeks")
                    if weeks_value:
                        try:
                            weeks_value = float(weeks_value)
                        except (ValueError, TypeError):
                            weeks_value = None

                    db_project = Project(
                        title=project_title,
                        description=project_item.get("description", ""),
                        learning_plan_id=plan.id,
                        weeks=weeks_value,
                        skills=project_item.get("skills") or [],
                        twists=project_item.get("twists") or [],
                        tips=project_item.get("tips") or [],
                        resources=project_item.get("resources") or [],
                        deadline=deadline_dt,
                        end_date=deadline_dt,
                        project_metadata=project_item.get("project_metadata") or {
                            "source": "learning_plan_generation",
                            "generated_at": datetime.now(timezone.utc).isoformat()
                        }
                    )
                    db.add(db_project)
                    db.commit()
                    db.refresh(db_project)

                if not db_project.start_date:
                    db_project.start_date = datetime.now(timezone.utc)

                if not db_project.end_date:
                    if db_project.deadline:
                        db_project.end_date = db_project.deadline
                    elif db_project.weeks:
                        start_week, end_week = self.parse_weeks_string(project_item.get("weeks"))
                        db_project.start_date = db_project.start_date + timedelta(weeks=start_week - 1)
                        db_project.end_date = db_project.start_date + timedelta(weeks=(end_week - start_week + 1))


                    else:
                        db_project.end_date = db_project.start_date + timedelta(weeks=1)

                db.commit()

                project_item["project_id"] = db_project.id
                project_item["status"] = db_project.status

                
                def get_task_phase(task: Task) -> str:
                    if task.completed:
                        return "completed"
                    elif task.due_date and task.due_date < datetime.now(timezone.utc):
                        return "review"
                    else:
                        return "in_progress"

                def get_project_phase_from_tasks(tasks: list[dict]) -> str:
                    if not tasks:
                        return "planning"
                    completed_count = sum(1 for t in tasks if t.get("completed"))
                    total_tasks = len(tasks)
                    if completed_count == 0:
                        return "planning"
                    elif completed_count < total_tasks:
                        return "in_progress"
                    else:
                        return "completed"


                enriched_tasks = []
                completed_count = 0
                total_score = 0

                for idx, task_desc in enumerate(project_item.get("tasks", [])):
                    # Standardize task data
                    if isinstance(task_desc, str):
                        task_data = {
                            "title": f"Task {idx+1}",
                            "description": task_desc,
                            "completed": False,
                            "status": "pending"
                        }
                    elif isinstance(task_desc, dict):
                        task_data = {
                            "title": task_desc.get("title") or f"Task {idx+1}",
                            "description": task_desc.get("description", ""),
                            "completed": task_desc.get("completed", False),
                            "status": task_desc.get("status", "pending")
                        }
                    else:
                        continue

                    
                    total_tasks = len(project_item.get("tasks", []))
                    task_deadline = None
                    if db_project.end_date and db_project.start_date:
                        total_seconds = (db_project.end_date - db_project.start_date).total_seconds()
                        seconds_per_task = total_seconds / total_tasks if total_tasks else 0
                        task_deadline = db_project.start_date + timedelta(seconds=seconds_per_task * (idx + 1))
                        task_data["due_date"] = task_deadline
                    else:
                        task_data["due_date"] = None

                    
                    if task_deadline:
                        days_left = (task_deadline - datetime.now(timezone.utc)).days
                        if days_left <= 1:
                            priority = "high"
                        elif days_left <= 3:
                            priority = "medium"
                        else:
                            priority = "low"
                    else:
                        priority = "medium"
                    task_data["priority"] = priority

                    
                    db_task = db.query(Task).filter(
                        Task.project_id == db_project.id,
                        Task.title == task_data["title"],
                        Task.description == task_data["description"]
                    ).first()

                    if not db_task:
                        db_task = Task(
                            project_id=db_project.id,
                            title=task_data["title"],
                            description=task_data["description"],
                            completed=task_data.get("completed", False),
                            status=task_data.get("status", "pending"),
                            due_date=task_deadline,
                            priority=task_data["priority"]
                        )
                        db.add(db_task)
                        db.commit()
                        db.refresh(db_task)
                    else:
                        if not db_task.due_date and task_deadline:
                            db_task.due_date = task_deadline
                            db.commit()
                            db.refresh(db_task)

                    # Update task priority based on due date
                    if db_task.due_date:
                        days_left = (db_task.due_date - datetime.now(timezone.utc)).days
                        if days_left <= 1:
                            db_task.priority = "high"
                        elif days_left <= 7:
                            db_task.priority = "medium"
                        else:
                            db_task.priority = "low"
                        db.commit()
                        db.refresh(db_task)

                    evaluation_report = None
                    submission = db.query(TaskSubmission).filter(
                          TaskSubmission.task_id == db_task.id,
                          TaskSubmission.user_id == plan.user_id
                    ).order_by(TaskSubmission.submitted_at.desc()).first()
                    evaluation_report = submission.evaluation_report if submission else None


                    if db_task.completed:
                     completed_count += 1
                    total_score += self.calculate_task_score(db_task)

                    enriched_tasks.append({
                        "task_id": db_task.id,
                        "title": db_task.title,
                        "description": db_task.description,
                        "completed": db_task.completed,
                        "status": db_task.status,
                        "phase": get_task_phase(db_task),
                        "due_date": db_task.due_date.isoformat() if db_task.due_date else None,
                        "priority": db_task.priority,
                        "evaluation_report": evaluation_report
                    })

                project_item["tasks"] = enriched_tasks
                project_item["total_tasks"] = len(enriched_tasks)
                project_item["completed_tasks"] = completed_count
                project_item["progress_percentage"] = round((completed_count / len(enriched_tasks)) * 100, 2) if enriched_tasks else 0
                project_item["average_score"] = round(total_score / len(enriched_tasks), 2) if enriched_tasks else 0
                project_item["phase"] = get_project_phase_from_tasks(enriched_tasks)
                project_status = self.determine_project_status(db_project)
                project_item["status"] = project_status
                # Sync DB
                if db_project.status != project_status:
                    db_project.status = project_status
                    db.commit()
                    db.refresh(db_project)



            plan_list.append(plan_dict)

        return plan_list

     except Exception as e:
        logger.error(f"Error getting learning plans: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    
    async def save_plan_feedback(
        self,
        plan_id: str,
        feedback: Dict,
        learning_service: LearningService = Depends(get_learning_service)
    ) -> Dict:
        """Save feedback for a learning plan."""
        try:
            result = await learning_service.save_feedback(plan_id, feedback)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Error saving feedback: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def save_learning_plan(
        self,
        plan: Dict,
        learning_service: LearningService = Depends(get_learning_service)
    ) -> Dict:
        """Save a learning plan."""
        try:
            result = await learning_service.save_plan(plan)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Error saving learning plan: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def create_learning_progress(
        self,
        progress: LearningProgressCreate,
        db: Session = Depends(get_db),
        learning_service: LearningService = Depends(get_learning_service)
    ) -> Dict:
        """Create a new learning progress entry."""
        try:
            result = await learning_service.create_progress(
                user_id=progress.user_id,
                topic_id=progress.topic_id,
                status=progress.status,
                completion_percentage=progress.completion_percentage,
                time_spent_minutes=progress.time_spent_minutes,
                notes=progress.notes
            )
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Error creating learning progress: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_learning_progress(
        self,
        progress_id: str,
        progress: LearningProgressUpdate,
        learning_service: LearningService = Depends(get_learning_service)
    ) -> Dict:
        """Update learning progress."""
        try:
            result = await learning_service.update_progress(
                progress_id=progress_id,
                update_data=progress.dict(exclude_none=True)
            )
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Error updating learning progress: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def create_learning_session(
        self,
        session: LearningSessionCreate,
        learning_service: LearningService = Depends(get_learning_service)
    ) -> Dict:
        """Create a new learning session."""
        try:
            result = await learning_service.create_session(
                user_id=session.user_id,
                start_time=session.start_time,
                end_time=session.end_time,
                topics=session.topics,
                learning_goals=session.learning_goals,
                achievements=session.achievements
            )
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Error creating learning session: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user_learning_progress(
        self,
        user_id: str,
        learning_service: LearningService = Depends(get_learning_service)
    ) -> Dict:
        """Get learning progress for a user."""
        try:
            progress = await learning_service.get_user_progress(user_id)
            return {"status": "success", "data": progress}
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_learning_analytics(
        self,
        user_id: str,
        learning_service: LearningService = Depends(get_learning_service)
    ) -> Dict:
        """Get learning analytics for a user."""
        try:
            analytics = await learning_service.get_analytics(user_id)
            return {"status": "success", "data": analytics}
        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_learning_metrics(
        self,
        user_id: str, 
        learning_service: LearningService = Depends(get_learning_service)
    ) -> Dict:
        """Get comprehensive learning metrics for a user."""
        try:
            metrics = await learning_service.get_learning_metrics(user_id)
            return metrics
        except Exception as e:
            logger.error(f"Error getting learning metrics: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_mentor_questions(self) -> Dict:
        """Get the questions the AI mentor needs to understand a user's profile"""
        # Static response of mentor profile questions
        return {
            "cognitive_style": {
                "title": "Understanding Your Thought Process",
                "description": "These questions help me understand how you approach problems and learn best",
                "questions": [
                    {
                        "id": "problem_solving",
                        "question": "When faced with a complex problem, how do you typically approach it?",
                        "type": "multiselect",
                        "reasoning": "Understanding your problem-solving approach helps me tailor explanations and project suggestions",
                        "options": [
                            "Break it down into smaller parts",
                            "Research similar problems first",
                            "Try different solutions through trial and error",
                            "Draw diagrams or visualize the problem",
                            "Discuss with others to get different perspectives",
                            "Start with what I know and build up gradually"
                        ]
                    },
                    {
                        "id": "learning_triggers",
                        "question": "What makes a topic or concept 'click' for you?",
                        "type": "multiselect",
                        "reasoning": "This helps me understand how to present information in a way that resonates with you",
                        "options": [
                            "Real-world examples and applications",
                            "Visual explanations and diagrams",
                            "Step-by-step breakdowns",
                            "Hands-on practice",
                            "Understanding the underlying theory",
                            "Teaching or explaining it to someone else"
                        ]
                    }
                ]
            },
            "background": {
                "title": "Your Experience and Knowledge",
                "description": "These questions help me gauge your current expertise and familiarity with different areas",
                "questions": [
                    {
                        "id": "tech_experience",
                        "question": "How would you describe your general technical background?",
                        "type": "select",
                        "reasoning": "This helps me adjust the level and amount of context I provide",
                        "options": [
                            "Complete beginner (little to no technical experience)",
                            "Some exposure (basic understanding of computers and software)",
                            "Intermediate (comfortable with technology, some programming experience)",
                            "Advanced (significant programming or technical experience)",
                            "Expert (professional experience in technical fields)"
                        ]
                    },
                    {
                        "id": "relevant_knowledge",
                        "question": "Which of these areas are you already familiar with?",
                        "type": "multiselect",
                        "reasoning": "This helps me avoid over-explaining concepts you already know",
                        "options": [
                            "Programming basics (variables, functions, loops)",
                            "Web development (HTML, CSS, JavaScript)",
                            "Backend development (servers, APIs, databases)",
                            "Data structures and algorithms",
                            "Mobile app development",
                            "Cloud services and deployment",
                            "Machine learning / AI concepts",
                            "Computer networking",
                            "Cybersecurity"
                        ]
                    }
                ]
            },
            "learning_preferences": {
                "title": "How You Prefer to Learn",
                "description": "These questions help me understand your ideal learning approach",
                "questions": [
                    {
                        "id": "pace_preference",
                        "question": "How do you prefer to progress through learning materials?",
                        "type": "select",
                        "reasoning": "This helps me adjust how quickly I introduce new concepts",
                        "options": [
                            "Deep dive (thoroughly master each concept before moving on)",
                            "Balanced (solid understanding before progressing)",
                            "Survey (get the big picture first, then fill in details)",
                            "Fast-track (focus on practical skills, learn theory as needed)"
                        ]
                    },
                    {
                        "id": "feedback_style",
                        "question": "What kind of feedback helps you learn best?",
                        "type": "multiselect",
                        "reasoning": "This helps me provide guidance in the most constructive way for you",
                        "options": [
                            "Detailed explanations of what went wrong",
                            "Gentle suggestions for improvement",
                            "Direct and straightforward correction",
                            "Examples of correct approaches",
                            "Questions that guide me to find my own mistakes",
                            "Positive reinforcement of what I did right"
                        ]
                    }
                ]
            }
        }

    async def submit_task(
     self,
     task_id: str,
     current_user: User = Depends(get_current_user_dependency),
     remark: str = Form(None),
     file: UploadFile = File(None),
     db: Session = Depends(get_db)
):
     try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        file_path = None
        if file:
            file_path = f"uploads/{task_id}_{file.filename}"
            with open(file_path, "wb") as f:
                f.write(await file.read())

        if not file_path and not remark:
            raise HTTPException(status_code=400, detail="Either file or remark must be provided")

        evaluation = evaluate_submission(file_path=file_path, remark=remark, task=task)
        score = evaluation.get("score", 0)

        
        submission = (
            db.query(TaskSubmission)
            .filter(TaskSubmission.task_id == task_id, TaskSubmission.user_id == current_user.id)
            .first()
        )

        if submission:
            
            submission.file_path = file_path
            submission.remark = remark
            submission.score = score
            submission.feedback = evaluation.get("feedback")
            submission.evaluation_report = evaluation
            submission.submitted_at = datetime.utcnow()
            submission.evaluated_at = datetime.utcnow()
        else:
            # Create new submission if not exist
            submission = TaskSubmission(
                task_id=task_id,
                user_id=current_user.id,
                file_path=file_path,
                remark=remark,
                score=score,
                feedback=evaluation.get("feedback"),
                evaluation_report=evaluation,
                status=TaskSubmissionStatus.EVALUATED,
                submitted_at=datetime.utcnow(),
                evaluated_at=datetime.utcnow(),
            )
            db.add(submission)

        
        if score >= 75:
            task.completed = True
            task.status = "completed"
            task.completed_at = datetime.utcnow()
        else:
            task.completed = False
            task.status = "pending"

        
        project = task.project
        project_just_completed = False
        if project:
            completed_tasks = sum(1 for t in project.tasks if t.completed)
            total_tasks = len(project.tasks)
            new_progress = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
            prev_progress = project.progress_percentage or 0
            project.progress_percentage = new_progress
            if new_progress == 100 and prev_progress < 100:
                project.status = "completed"
                project_just_completed = True
            db.add(project)

        db.commit()
        db.refresh(submission)
        db.refresh(task)

        # Auto-trigger discovery conversation when project reaches 100%
        if project_just_completed and project:
            try:
                from ..services.assessment_service import trigger_discovery
                trigger_discovery(
                    db=db,
                    project_id=project.id,
                    user_id=current_user.id,
                    reason="completed",
                )
                logger.info("Discovery triggered for completed project %s", project.id)
            except ValueError:
                # Discovery already exists — idempotent, safe to ignore
                pass
            except Exception as exc:
                logger.error("Failed to auto-trigger discovery for project %s: %s", project.id, exc)

        return {
            "message": "Task submitted successfully",
            "submission_id": submission.id,
            "evaluation_report": submission.evaluation_report,
            "task_status": task.status,
            "project_progress": project.progress_percentage if project else None,
            "discovery_triggered": project_just_completed,
        }

     except HTTPException:
        raise
     except Exception as e:
        db.rollback()
        logger.error(f"Error submitting task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Create and export the router object with backward compatibility structure
router = LearningRouter()