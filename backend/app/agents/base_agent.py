"""
Base agent class for all specialized agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, user_context: Dict[str, Any], db_session=None):
        """
        Initialize the base agent.
        
        Args:
            user_context: Dictionary containing user information
            db_session: Database session for data operations
        """
        self.user_context = user_context
        self.db = db_session
        
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        Returns:
            String containing the system prompt
        """
        pass
    
    @abstractmethod
    def get_agent_name(self) -> str:
        """
        Get the name of this agent for logging purposes.
        
        Returns:
            String name of the agent
        """
        pass
    
    def get_base_context(self) -> str:
        """
        Get common context that all agents can use.
        
        Returns:
            String containing base context information
        """
        context_parts = []
        
        if self.user_context.get('name'):
            context_parts.append(f"User Name: {self.user_context['name']}")
            
        if self.user_context.get('skill_level'):
            context_parts.append(f"Skill Level: {self.user_context['skill_level']}")
            
        if self.user_context.get('interests'):
            interests = self.user_context['interests']
            if isinstance(interests, list):
                context_parts.append(f"Interests: {', '.join(interests)}")
            else:
                context_parts.append(f"Interests: {interests}")
                
        if self.user_context.get('career_path'):
            context_parts.append(f"Career Path: {self.user_context['career_path']}")

        interest_ctx = self.get_interest_context()
        if interest_ctx:
            context_parts.append(interest_ctx)

        session_ctx = self.get_session_continuity_context()
        if session_ctx:
            context_parts.append(session_ctx)

        return "\n".join(context_parts) if context_parts else "No user context available."

    def get_session_continuity_context(self) -> str:
        """
        Build a session-continuity block from prior_session_context stored
        in user_context by message_service.

        Returns an empty string for first-time users or when no prior context exists.
        """
        prior = self.user_context.get('prior_session_context')
        if not prior or not prior.get('is_returning_user'):
            return ""

        parts = []
        summary = prior.get('prior_summary', '')
        if summary:
            parts.append(summary)

        topics = prior.get('last_session_topics', [])
        if topics:
            parts.append(f"Key topics from last session: {', '.join(topics)}")

        last_at = prior.get('last_session_at')
        if last_at:
            parts.append(f"Last session ended: {last_at}")

        return "\n".join(parts) if parts else ""

    def get_interest_context(self) -> str:
        """
        Build a concise interest-profile string from the structured interest data
        stored in user_context['interest_profile'].

        Returns an empty string when no meaningful profile is available (confidence < 0.2).
        """
        profile = self.user_context.get('interest_profile')
        if not profile:
            return ""

        confidence = profile.get('confidence_level', 0.0)
        if confidence < 0.2:
            return "Interest profile: still learning about this user."

        parts = []
        domains = profile.get('domains', {})
        if domains:
            # Sort by weight descending, show top 5
            top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]
            parts.append("User interest domains: " + ", ".join(d for d, _ in top_domains))

        strengths = profile.get('strengths', [])
        if strengths:
            parts.append("Strengths: " + ", ".join(strengths[:5]))

        aversions = profile.get('aversions', [])
        if aversions:
            parts.append("Dislikes/aversions: " + ", ".join(aversions[:3]))

        ls = profile.get('learning_style')
        if ls:
            parts.append(f"Learning style: {ls}")

        return "\n".join(parts) if parts else ""
    
    def get_learning_plans_context(self) -> str:
        """
        Get learning plans context for the agent.
        
        Returns:
            String containing learning plans information
        """
        learning_plans = self.user_context.get('learning_plans', [])
        
        if not learning_plans:
            return "No learning plans available."
            
        context_parts = []
        for i, plan in enumerate(learning_plans[:3]):  # Limit to 3 most recent plans
            title = plan.get('title', 'Untitled Plan')
            description = plan.get('description', 'No description')
            projects = plan.get('projects', [])
            
            context_parts.append(f"Learning Plan {i+1}: {title}")
            context_parts.append(f"Description: {description}")
            
            if projects:
                context_parts.append(f"Projects ({len(projects)}):")
                for j, project in enumerate(projects[:3]):  # Limit to 3 projects
                    project_title = project.get('title', f'Project {j+1}')
                    context_parts.append(f"  - {project_title}")
                    
                    if project.get('tasks'):
                        context_parts.append(f"    Tasks: {len(project['tasks'])} tasks defined")
            
            context_parts.append("")  # Empty line between plans
            
        return "\n".join(context_parts)
    
    def get_learning_progress_context(self) -> str:
        """
        Get context about the user's learning progress and recent activities.
        
        Returns:
            String containing progress information
        """
        learning_plans = self.user_context.get('learning_plans', [])
        
        if not learning_plans:
            return "User is just starting their learning journey."
            
        current_plan = learning_plans[0]
        projects = current_plan.get('projects', [])
        
        context_parts = [
            f"Currently working on: {current_plan.get('title', 'Learning Plan')}",
        ]
        
        if projects:
            # Assume progress on first project for demo
            current_project = projects[0]
            context_parts.append(f"Active project: {current_project.get('title', 'Project')}")
            
            tasks = current_project.get('tasks', [])
            if tasks:
                context_parts.append(f"Total tasks in current project: {len(tasks)}")
                # In production, you'd track actual completion status
                context_parts.append("Progress tracking available for detailed guidance")
        
        # Add learning patterns and preferences
        context_parts.extend([
            "",
            "Learning characteristics:",
            f"• Preferred learning style: {self.user_context.get('learning_style', 'Not specified')}",
            f"• Current skill level: {self.user_context.get('skill_level', 'Not specified')}",
            f"• Main interests: {', '.join(self.user_context.get('interests', ['Not specified']))}"
        ])
        
        return "\n".join(context_parts)
    
    def format_response(self, response: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format the agent response with metadata.
        
        Args:
            response: The response text
            metadata: Optional metadata to include
            
        Returns:
            Dictionary containing formatted response
        """
        formatted = {
            "text": response,
            "agent": self.get_agent_name(),
            "timestamp": None  # Will be set by the message service
        }
        
        if metadata:
            formatted.update(metadata)
            
        return formatted
    
    def log_interaction(self, message: str, response: str) -> None:
        """
        Log the interaction for debugging and monitoring.
        
        Args:
            message: User message
            response: Agent response
        """
        logger.info(f"{self.get_agent_name()} processed message: {message[:100]}...")
        logger.info(f"{self.get_agent_name()} response length: {len(response)} characters")
    
    def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message and return enhanced context.
        This is a default implementation that subclasses can override.
        
        Args:
            message: User message
            context: Current context
            
        Returns:
            Enhanced context dictionary
        """
        return {
            **context,
            'agent_name': self.get_agent_name(),
            'system_prompt': self.get_system_prompt()
        } 