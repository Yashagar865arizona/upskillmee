"""
Learning Plan Schema
Defines the schema for learning plans
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

class LearningPlanTask(BaseModel):
    """Task within a learning plan project"""
    title: str = Field(..., description="Task title")
    completed: bool = Field(default=False, description="Whether the task is completed")

class LearningPlanResource(BaseModel):
    """Resource within a learning plan project"""
    title: str = Field(..., description="Resource title")
    url: Optional[str] = Field(default=None, description="Resource URL if available")

class LearningPlanSkill(BaseModel):
    """Skill within a learning plan project"""
    name: str = Field(..., description="Skill name")

class LearningPlanProject(BaseModel):
    """Project within a learning plan"""
    title: str = Field(..., description="Project title")
    description: str = Field(..., description="Project description")
    tasks: List[str] = Field(default_factory=list, description="List of tasks")
    skills: List[str] = Field(default_factory=list, description="List of skills to develop")
    resources: List[str] = Field(default_factory=list, description="List of resources")
    weeks: str = Field(..., description="Timeframe for the project")

class LearningPlan(BaseModel):
    """Learning plan schema"""
    title: str = Field(..., description="Learning plan title")
    description: str = Field(..., description="Learning plan description")
    projects: List[LearningPlanProject] = Field(..., description="List of projects in the learning plan")

    @field_validator('projects')
    @classmethod
    def validate_projects(cls, projects):
        """Ensure there is at least one project"""
        if not projects:
            raise ValueError("Learning plan must have at least one project")
        return projects

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "JavaScript Basics Learning Plan",
                "description": "A structured approach to learning JavaScript fundamentals with hands-on projects",
                "projects": [
                    {
                        "title": "Project 1: Interactive To-Do List",
                        "description": "Build a simple to-do list application to learn DOM manipulation",
                        "tasks": ["Set up HTML structure", "Style with CSS", "Add JavaScript functionality"],
                        "skills": ["DOM manipulation", "Event handling", "Local storage"],
                        "resources": ["MDN Web Docs", "W3Schools JavaScript Tutorial", "JavaScript.info"],
                        "weeks": "Week 1-2"
                    }
                ]
            }
        }
    )
