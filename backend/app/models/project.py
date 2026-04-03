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
    portfolio_summary = Column(String, nullable=True)  # Cached AI-generated portfolio summary


    # Relationships
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    learning_plan = relationship("LearningPlan", back_populates="projects")
    assessments = relationship("ProjectAssessment", back_populates="project", cascade="all, delete-orphan")
    discoveries = relationship("PostProjectDiscovery", back_populates="project", cascade="all, delete-orphan")

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


class ProjectAssessment(BaseModel, Base):
    __tablename__ = "project_assessments"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    score = Column(INTEGER, nullable=False)  # 0-100
    completeness_score = Column(INTEGER, nullable=True)
    quality_score = Column(INTEGER, nullable=True)
    skill_alignment_score = Column(INTEGER, nullable=True)
    feedback = Column(String, nullable=True)
    strengths = Column(ARRAY(String), default=list)
    improvements = Column(ARRAY(String), default=list)
    next_steps = Column(ARRAY(String), default=list)
    recommended_topics = Column(ARRAY(String), default=list)
    assessment_report = Column(JSON, default=dict)
    assessed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    project = relationship("Project", back_populates="assessments")


class PostProjectDiscovery(BaseModel, Base):
    """
    Discovery conversation record created after a project is completed or abandoned.

    The AI asks the user what they enjoyed, what they struggled with, and whether
    they'd continue in that direction. Structured responses feed the interest model.
    """
    __tablename__ = "post_project_discoveries"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    trigger_reason = Column(String, nullable=False)  # "completed" | "abandoned"
    triggered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # AI conversation starter returned to the frontend
    conversation_starter = Column(String, nullable=True)

    # Structured data extracted from user response
    enjoyed_aspects = Column(String, nullable=True)
    struggled_aspects = Column(String, nullable=True)
    would_continue = Column(Boolean, nullable=True)
    engagement_score = Column(INTEGER, nullable=True)  # 1-5, AI-inferred
    domains_confirmed = Column(JSON, default=list)
    domains_rejected = Column(JSON, default=list)

    project = relationship("Project", back_populates="discoveries")


class DiscoveryReport(BaseModel, Base):
    """
    Cached self-discovery report generated after a user completes 3+ assessed projects.

    Contains interest patterns, strength signals, domains explored, and pivot
    suggestions. A unique share_token enables public read-only access.
    """
    __tablename__ = "discovery_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    share_token = Column(String, unique=True, nullable=False, index=True)

    # Report sections (all JSON)
    interest_patterns = Column(JSON, default=dict)
    strength_signals = Column(JSON, default=dict)
    domains_explored = Column(JSON, default=dict)
    pivot_suggestions = Column(JSON, default=dict)

    # Narrative summaries generated by LLM
    narrative_summary = Column(String, nullable=True)

    # Cache invalidation
    project_count_at_generation = Column(INTEGER, nullable=False, default=0)
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
