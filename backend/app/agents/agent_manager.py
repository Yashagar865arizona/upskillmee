"""
Agent Manager for orchestrating different specialized agents.
"""

from enum import Enum
from typing import Dict, Any, Optional
import logging
from .plan_agent import LearningPlanAgent
from .work_agent import ProjectWorkAgent
from .chat_agent import ChatAgent

logger = logging.getLogger(__name__)

class AgentMode(Enum):
    """Enumeration of available agent modes."""
    PLAN = "plan"
    WORK = "work" 
    CHAT = "chat"

class AgentManager:
    """Manager for coordinating different specialized agents."""
    
    def __init__(self, db_session, user_context: Dict[str, Any]):
        """
        Initialize the agent manager.
        
        Args:
            db_session: Database session for data operations
            user_context: User context information
        """
        self.db = db_session
        self.user_context = user_context
        
        # Initialize all agents
        self.agents = {
            AgentMode.PLAN: LearningPlanAgent(user_context, db_session),
            AgentMode.WORK: ProjectWorkAgent(user_context, db_session),
            AgentMode.CHAT: ChatAgent(user_context, db_session)
        }
        
        logger.info(f"AgentManager initialized with {len(self.agents)} agents")
    
    def process_message(self, message: str, mode: AgentMode, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message using the appropriate agent.
        
        Args:
            message: User message to process
            mode: Agent mode to use
            context: Additional context information
            
        Returns:
            Enhanced context with agent-specific information
        """
        try:
            # Get the appropriate agent
            agent = self.agents.get(mode)
            if not agent:
                logger.error(f"No agent found for mode: {mode}")
                # Fallback to chat agent
                agent = self.agents[AgentMode.CHAT]
                mode = AgentMode.CHAT
            
            logger.info(f"Processing message with {agent.get_agent_name()} in {mode.value} mode")
            
            # Add mode-specific context enhancement
            enhanced_context = self._enhance_context_for_mode(context, mode, message)
            
            # Process the message with the agent (returns enhanced context)
            agent_context = agent.process_message(message, enhanced_context)
            
            # Merge contexts
            final_context = {
                **enhanced_context,
                **agent_context,
                'mode': mode.value
            }
            
            # Log the interaction
            agent.log_interaction(message, f"Context enhanced for {mode.value} mode")
            
            return final_context
            
        except Exception as e:
            logger.error(f"Error processing message in {mode.value} mode: {str(e)}")
            # Fallback to basic context
            return {
                **context,
                'error': f"Agent processing error: {str(e)}",
                'mode': mode.value,
                'system_prompt': self._get_fallback_prompt(mode)
            }
    
    def _enhance_context_for_mode(self, context: Dict[str, Any], mode: AgentMode, message: str) -> Dict[str, Any]:
        """
        Add mode-specific context enhancements.
        
        Args:
            context: Base context
            mode: Agent mode
            message: User message
            
        Returns:
            Enhanced context with mode-specific information
        """
        enhanced = {**context}
        
        if mode == AgentMode.WORK:
            enhanced.update({
                'current_project_details': self._get_current_project_details(),
                'technical_assistance_mode': True,
                'code_examples_enabled': True,
                'step_by_step_guidance': True
            })
            
        elif mode == AgentMode.PLAN:
            enhanced.update({
                'learning_preferences': self._get_learning_preferences(),
                'plan_creation_mode': True,
                'structured_output_enabled': True,
                'goal_setting_focus': True
            })
            
        elif mode == AgentMode.CHAT:
            enhanced.update({
                'conversational_mode': True,
                'mentoring_enabled': True,
                'emotional_support': True,
                'personal_connection': True
            })
        
        # Add common enhancements
        enhanced.update({
            'message_analysis': self._analyze_message(message),
            'user_preferences': self._get_user_preferences(),
            'session_context': self._get_session_context()
        })
        
        return enhanced
    
    def _get_current_project_details(self) -> Dict[str, Any]:
        """Get detailed information about the current project."""
        learning_plans = self.user_context.get('learning_plans', [])
        
        if not learning_plans:
            return {'status': 'no_active_project'}
            
        current_plan = learning_plans[0]
        projects = current_plan.get('projects', [])
        
        if not projects:
            return {'status': 'no_projects_in_plan'}
            
        # For now, assume working on first project
        # In production, track actual progress
        current_project = projects[0]
        
        return {
            'status': 'active_project',
            'project_title': current_project.get('title', 'Untitled'),
            'project_description': current_project.get('description', ''),
            'tasks': current_project.get('tasks', []),
            'resources': current_project.get('resources', []),
            'skills': current_project.get('skills', []),
            'total_projects': len(projects),
            'current_project_index': 0  # Would track actual progress
        }
    
    def _get_learning_preferences(self) -> Dict[str, Any]:
        """Get user's learning preferences and patterns."""
        return {
            'skill_level': self.user_context.get('skill_level', 'beginner'),
            'learning_style': self.user_context.get('learning_style', 'hands-on'),
            'interests': self.user_context.get('interests', []),
            'career_path': self.user_context.get('career_path', ''),
            'time_availability': self.user_context.get('time_availability', 'moderate'),
            'preferred_pace': self.user_context.get('preferred_pace', 'steady')
        }
    
    def _get_user_preferences(self) -> Dict[str, Any]:
        """Get general user preferences for communication style."""
        return {
            'communication_style': self.user_context.get('communication_style', 'friendly'),
            'detail_level': self.user_context.get('detail_level', 'moderate'),
            'encouragement_level': self.user_context.get('encouragement_level', 'high'),
            'technical_depth': self.user_context.get('technical_depth', 'practical')
        }
    
    def _get_session_context(self) -> Dict[str, Any]:
        """Get context about the current session."""
        return {
            'session_start': None,  # Would track session timing
            'messages_in_session': 0,  # Would count messages
            'previous_mode': None,  # Would track mode switching
            'user_engagement': 'active'  # Would assess engagement
        }
    
    def _analyze_message(self, message: str) -> Dict[str, Any]:
        """Analyze the message for content and intent."""
        message_lower = message.lower()
        
        # Detect urgency
        urgency_indicators = ['urgent', 'asap', 'quickly', 'fast', 'immediately']
        is_urgent = any(indicator in message_lower for indicator in urgency_indicators)
        
        # Detect complexity
        complexity_indicators = ['complex', 'advanced', 'difficult', 'challenging']
        is_complex = any(indicator in message_lower for indicator in complexity_indicators)
        
        # Detect question type
        if message.strip().endswith('?'):
            question_type = 'direct_question'
        elif any(word in message_lower for word in ['how', 'what', 'why', 'when', 'where']):
            question_type = 'information_seeking'
        elif any(word in message_lower for word in ['help', 'assist', 'guide']):
            question_type = 'assistance_request'
        else:
            question_type = 'statement'
        
        return {
            'length': len(message),
            'word_count': len(message.split()),
            'is_urgent': is_urgent,
            'is_complex': is_complex,
            'question_type': question_type,
            'contains_code': '```' in message or 'function' in message_lower
        }
    
    def _get_fallback_prompt(self, mode: AgentMode) -> str:
        """Get a basic fallback prompt if agent initialization fails."""
        base_prompts = {
            AgentMode.PLAN: "You are a learning plan assistant. Help create and manage learning plans.",
            AgentMode.WORK: "You are a technical mentor. Provide step-by-step coding guidance.",
            AgentMode.CHAT: "You are a learning companion. Provide encouragement and support."
        }
        
        return base_prompts.get(mode, "You are a helpful AI assistant.")
    
    def suggest_mode_switch(self, message: str, current_mode: AgentMode) -> Optional[AgentMode]:
        """
        Suggest a mode switch based on message content.
        
        Args:
            message: User message
            current_mode: Current agent mode
            
        Returns:
            Suggested mode or None if no switch recommended
        """
        message_lower = message.lower()
        
        # Keywords that suggest specific modes
        plan_keywords = ['create plan', 'new plan', 'learning plan', 'curriculum', 'roadmap']
        work_keywords = ['help with', 'how to implement', 'code', 'debug', 'error', 'step by step']
        chat_keywords = ['how are you', 'motivation', 'career', 'feeling', 'advice']
        
        # Check for mode switch indicators
        if current_mode != AgentMode.PLAN and any(keyword in message_lower for keyword in plan_keywords):
            return AgentMode.PLAN
        elif current_mode != AgentMode.WORK and any(keyword in message_lower for keyword in work_keywords):
            return AgentMode.WORK
        elif current_mode != AgentMode.CHAT and any(keyword in message_lower for keyword in chat_keywords):
            return AgentMode.CHAT
        
        return None
    
    def get_available_modes(self) -> Dict[str, str]:
        """Get information about available modes."""
        return {
            'plan': 'Create and edit learning plans',
            'work': 'Get technical help with projects',
            'chat': 'General conversation and mentoring'
        } 