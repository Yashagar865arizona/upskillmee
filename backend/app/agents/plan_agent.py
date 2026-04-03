"""
Learning Plan Agent for creating and managing learning plans.
"""

from typing import Dict, Any
from .base_agent import BaseAgent

class LearningPlanAgent(BaseAgent):
    """Agent specialized in creating and managing learning plans."""
    
    def get_agent_name(self) -> str:
        return "LearningPlanAgent"
    
    def get_system_prompt(self) -> str:
        """Get system prompt optimized for learning plan creation."""
        
        base_context = self.get_base_context()
        learning_context = self.get_learning_plans_context()
        
        return f"""You are a Learning Plan Specialist and Educational Architect. Your expertise lies in creating comprehensive, structured, and personalized learning plans that maximize student success.

CORE RESPONSIBILITIES:
• Create detailed learning plans with clear progression paths
• Break down complex topics into manageable, sequential projects
• Design practical, hands-on learning experiences
• Provide realistic timelines and milestones
• Adapt content to user's skill level and learning style
• Ensure each project builds upon previous knowledge

CURRENT USER CONTEXT:
{base_context}

EXISTING LEARNING PLANS:
{learning_context}

PLAN STRUCTURE REQUIREMENTS:
When creating or editing plans, always include:

1. PLAN OVERVIEW
   - Clear title and description
   - Target skill level and prerequisites
   - Estimated completion time
   - Learning objectives

2. PROJECT BREAKDOWN
   - 3-6 progressive projects
   - Each project should have:
     * Clear title and description
     * Specific learning objectives
     * 4-8 concrete tasks
     * Required resources and tools
     * Skills learned/practiced
     * Estimated time commitment

3. TASK DETAILS
   - Step-by-step instructions
   - Code examples when relevant
   - Resources and references
   - Success criteria

RESPONSE STYLE:
• Be specific and actionable
• Focus on practical implementation
• Use clear, structured formatting
• Provide realistic expectations
• Include motivational elements
• Reference user's interests and goals

WHEN USER ASKS TO:
• "Create a plan" → Generate complete structured plan
• "Edit plan" → Modify existing plan with specific changes
• "Add project" → Insert new project maintaining progression
• "Update timeline" → Adjust deadlines and milestones

Remember: Learning plans should be challenging but achievable, with each project building confidence and skills for the next level."""

    def get_current_plan_context(self) -> str:
        """Get detailed context about the current plan being worked on."""
        learning_plans = self.user_context.get('learning_plans', [])
        
        if not learning_plans:
            return "No current learning plan. Ready to create a new one."
            
        current_plan = learning_plans[0]  # Most recent plan
        
        context_parts = [
            f"CURRENT PLAN: {current_plan.get('title', 'Untitled')}",
            f"Description: {current_plan.get('description', 'No description')}",
            ""
        ]
        
        projects = current_plan.get('projects', [])
        if projects:
            context_parts.append(f"PROJECTS ({len(projects)}):")
            for i, project in enumerate(projects, 1):
                title = project.get('title', f'Project {i}')
                description = project.get('description', 'No description')
                tasks = project.get('tasks', [])
                
                context_parts.append(f"{i}. {title}")
                context_parts.append(f"   Description: {description}")
                if tasks:
                    context_parts.append(f"   Tasks: {len(tasks)} defined")
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message with learning plan focus."""
        # This would integrate with your AI service
        # For now, returning the system prompt setup
        enhanced_context = {
            **context,
            'agent_mode': 'plan',
            'current_plan_details': self.get_current_plan_context(),
            'plan_creation_guidelines': self._get_plan_guidelines(),
            'system_prompt': self.get_system_prompt(),
            'agent_name': self.get_agent_name()
        }
        
        return enhanced_context
    
    def _get_plan_guidelines(self) -> Dict[str, Any]:
        """Get guidelines for plan creation based on user skill level."""
        skill_level = self.user_context.get('skill_level', 'beginner')
        
        guidelines = {
            'beginner': {
                'project_count': '3-4',
                'task_complexity': 'Simple, well-explained steps',
                'time_per_project': '1-2 weeks',
                'focus': 'Building fundamentals and confidence'
            },
            'intermediate': {
                'project_count': '4-5', 
                'task_complexity': 'Moderate complexity with challenges',
                'time_per_project': '2-3 weeks',
                'focus': 'Practical applications and problem-solving'
            },
            'advanced': {
                'project_count': '4-6',
                'task_complexity': 'Complex, real-world scenarios',
                'time_per_project': '2-4 weeks', 
                'focus': 'Advanced concepts and optimization'
            }
        }
        
        return guidelines.get(skill_level, guidelines['beginner']) 