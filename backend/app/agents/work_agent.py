"""
Project Work Agent for providing technical guidance and project assistance.
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent

class ProjectWorkAgent(BaseAgent):
    """Agent specialized in providing technical project guidance and assistance."""
    
    def get_agent_name(self) -> str:
        return "ProjectWorkAgent"
    
    def get_system_prompt(self) -> str:
        """Get system prompt optimized for technical project assistance."""
        
        base_context = self.get_base_context()
        current_project = self.get_current_project_context()
        
        return f"""You are a Technical Project Mentor and Coding Instructor. Your expertise lies in providing clear, practical, step-by-step guidance for coding projects and technical challenges.

CORE RESPONSIBILITIES:
• Provide detailed technical explanations and guidance
• Break down complex coding tasks into manageable steps
• Explain concepts clearly with practical examples
• Help debug code and solve specific technical problems
• Give actionable, implementable advice
• Focus on best practices and clean code
• Adapt explanations to user's skill level

CURRENT USER CONTEXT:
{base_context}

CURRENT PROJECT CONTEXT:
{current_project}

RESPONSE GUIDELINES:

1. TECHNICAL EXPLANATIONS
   - Start with clear, simple explanations
   - Provide concrete code examples
   - Explain the "why" behind each step
   - Include expected outputs/results
   - Mention common pitfalls to avoid

2. STEP-BY-STEP GUIDANCE
   - Break complex tasks into smaller steps
   - Number each step clearly
   - Provide code snippets for each step
   - Include testing/verification steps
   - Show how to debug if things go wrong

3. CODE EXAMPLES
   - Always include complete, runnable code
   - Add clear comments explaining each part
   - Show before/after examples when relevant
   - Include file structure when needed
   - Provide multiple approaches when beneficial

4. DEBUGGING HELP
   - Ask clarifying questions about the specific error
   - Explain common causes of the problem
   - Provide systematic debugging steps
   - Show how to test the solution
   - Suggest prevention strategies

WHEN USER ASKS FOR:
• "Help with task X" → Provide step-by-step implementation guide
• "Explain this concept" → Give clear explanation with examples
• "Debug this code" → Analyze and provide fixing steps
• "Best practices" → Suggest improvements and optimizations
• "How to implement" → Show complete implementation approach

RESPONSE STYLE:
• Be direct and technically accurate
• Use code examples liberally
• Explain technical terms when first used
• Provide alternative approaches when helpful
• Include resources for further learning
• Be encouraging but realistic about complexity

Remember: Focus on practical implementation. The user wants to actually build something, not just understand theory."""

    def get_current_project_context(self) -> str:
        """Get detailed context about the current project being worked on."""
        learning_plans = self.user_context.get('learning_plans', [])
        
        if not learning_plans:
            return "No active project. Ready to help with any coding task or project."
            
        current_plan = learning_plans[0]
        projects = current_plan.get('projects', [])
        
        if not projects:
            return "No projects in current learning plan."
            
        # For now, assume user is working on the first project
        # In production, you'd track current project progress
        current_project = projects[0]
        
        context_parts = [
            f"CURRENT PROJECT: {current_project.get('title', 'Untitled Project')}",
            f"Description: {current_project.get('description', 'No description')}",
            ""
        ]
        
        # Add task details
        tasks = current_project.get('tasks', [])
        if tasks:
            context_parts.append(f"PROJECT TASKS ({len(tasks)}):")
            for i, task in enumerate(tasks, 1):
                if isinstance(task, str):
                    context_parts.append(f"{i}. {task}")
                elif isinstance(task, dict):
                    task_title = task.get('title', f'Task {i}')
                    context_parts.append(f"{i}. {task_title}")
                    if task.get('description'):
                        context_parts.append(f"   {task['description']}")
            context_parts.append("")
        
        # Add resources and skills
        if current_project.get('resources'):
            resources = current_project['resources']
            context_parts.append("RESOURCES:")
            if isinstance(resources, list):
                for resource in resources:
                    context_parts.append(f"• {resource}")
            else:
                context_parts.append(f"• {resources}")
            context_parts.append("")
            
        if current_project.get('skills'):
            skills = current_project['skills']
            context_parts.append("SKILLS TO LEARN:")
            if isinstance(skills, list):
                for skill in skills:
                    context_parts.append(f"• {skill}")
            else:
                context_parts.append(f"• {skills}")
        
        return "\n".join(context_parts)
    
    def get_technical_context(self, message: str) -> Dict[str, Any]:
        """Analyze message to provide relevant technical context."""
        message_lower = message.lower()
        
        # Detect programming language/technology
        tech_keywords = {
            'html': ['html', 'markup', 'tags', 'elements'],
            'css': ['css', 'styling', 'styles', 'design'],
            'javascript': ['javascript', 'js', 'function', 'event'],
            'python': ['python', 'py', 'django', 'flask'],
            'react': ['react', 'jsx', 'component', 'hook'],
            'node': ['node', 'npm', 'express', 'server']
        }
        
        detected_tech = []
        for tech, keywords in tech_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_tech.append(tech)
        
        # Detect task type
        task_keywords = {
            'debugging': ['error', 'bug', 'broken', 'not working', 'debug'],
            'implementation': ['how to', 'implement', 'create', 'build', 'make'],
            'explanation': ['explain', 'what is', 'how does', 'why'],
            'optimization': ['improve', 'optimize', 'better', 'performance']
        }
        
        task_type = 'general'
        for task, keywords in task_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                task_type = task
                break
        
        return {
            'detected_technologies': detected_tech,
            'task_type': task_type,
            'complexity_indicators': self._assess_complexity(message)
        }
    
    def _assess_complexity(self, message: str) -> Dict[str, Any]:
        """Assess the complexity level of the user's request."""
        message_lower = message.lower()
        
        beginner_indicators = ['basic', 'simple', 'first time', 'beginner', 'start']
        advanced_indicators = ['advanced', 'complex', 'optimization', 'performance', 'architecture']
        
        complexity = 'intermediate'  # Default
        
        if any(indicator in message_lower for indicator in beginner_indicators):
            complexity = 'beginner'
        elif any(indicator in message_lower for indicator in advanced_indicators):
            complexity = 'advanced'
            
        return {
            'level': complexity,
            'requires_examples': complexity in ['beginner', 'intermediate'],
            'requires_deep_explanation': complexity == 'beginner'
        }
    
    def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message with technical project focus."""
        technical_context = self.get_technical_context(message)
        
        enhanced_context = {
            **context,
            'agent_mode': 'work',
            'current_project_details': self.get_current_project_context(),
            'technical_context': technical_context,
            'code_assistance_mode': True,
            'system_prompt': self.get_system_prompt(),
            'agent_name': self.get_agent_name()
        }
        
        return enhanced_context 