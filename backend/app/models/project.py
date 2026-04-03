import enum
from sqlalchemy import ARRAY, Column, String, DateTime, ForeignKey, Enum as SQLEnum, JSON, Boolean, INTEGER
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.base import Base
from .base_model import BaseModel
from uuid import uuid4

class ProjectPhase(enum.Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"

class TaskSubmissionStatus(enum.Enum):
    PENDING = "pending",        
    PROCESSING = "processing",  
    EVALUATED = "evaluated",    
    FAILED = "failed",          
    RESUBMIT_REQUIRED = "resubmit_required" 


class Project(BaseModel, Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    learning_plan_id = Column(String, ForeignKey("learning_plans.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="active")
    phase = Column(
        SQLEnum(ProjectPhase, name="projectphase"),
        default=ProjectPhase.PLANNING,
        nullable=False
    )
    start_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    end_date = Column(DateTime(timezone=True))
    weeks = Column(String, nullable=True)
    skills = Column(ARRAY(String), default=list)
    twists = Column(ARRAY(String), default=list)
    tips = Column(ARRAY(String), default=list)
    resources = Column(ARRAY(String), default=list)
    deadline = Column(DateTime(timezone=True), nullable=True)
    progress_percentage = Column(INTEGER, default=0)
    project_metadata = Column(JSON, default=dict, nullable=False)


    # Relationships
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    learning_plan = relationship("LearningPlan", back_populates="projects")

class Task(BaseModel, Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    # task_id = Column(String, unique=True, nullable=False, default=lambda: str(uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="pending")
    priority = Column(String, default="medium")
    due_date = Column(DateTime(timezone=True))
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="tasks")
    task_submissions = relationship("TaskSubmission", back_populates="task", cascade="all, delete-orphan")

class Milestone(BaseModel, Base):
    __tablename__ = "milestones"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    title = Column(String, nullable=False)
    description = Column(String)
    target_date = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    project = relationship("Project", back_populates="milestones")

class TaskSubmission(BaseModel, Base):
    __tablename__= "task_submission"

    id =Column(String, primary_key=True, index= True, default=lambda: str(uuid4()))
    task_id =Column(String, ForeignKey("tasks.id"))
    user_id = Column(String, ForeignKey("users.id"))
    file_path =Column(String, nullable=True)
    remark=Column(String, nullable=True)
    submitted_at=Column(DateTime(timezone=True), nullable=True)
    score=Column(String, nullable=True)
    feedback=Column(String, nullable=True)
    status=Column(
        SQLEnum(TaskSubmissionStatus, name="tasksubmissionstatus"),
        default=TaskSubmissionStatus.PENDING,
        nullable=False
    )
    evaluation_report=Column(JSON, default=dict)
    evaluated_at=Column(DateTime(timezone=True), nullable=True)

    task = relationship("Task", back_populates="task_submissions")
