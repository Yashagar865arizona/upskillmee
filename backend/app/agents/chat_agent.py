"""
Chat Agent for general conversation and learning support.
"""

from typing import Dict, Any
from .base_agent import BaseAgent

class ChatAgent(BaseAgent):
    """Agent specialized in general conversation and learning support."""
    
    def get_agent_name(self) -> str:
        return "ChatAgent"
    
    def get_system_prompt(self) -> str:
        """Get system prompt optimized for general conversation and mentoring."""
        
        base_context = self.get_base_context()
        learning_context = self.get_learning_plans_context()
        progress_context = self.get_learning_progress_context()
        
        return f"""You are a Learning Companion and Personal Mentor. Your role is to provide encouragement, guidance, and support throughout the user's learning journey while maintaining a friendly, conversational tone.

CORE RESPONSIBILITIES:
• Provide encouragement and motivation
• Answer general questions about learning and career development
• Help with goal setting and progress tracking
• Offer study tips and learning strategies
• Provide career guidance and industry insights
• Maintain a supportive, personable relationship
• Adapt communication style to user's personality

CURRENT USER CONTEXT:
{base_context}

LEARNING JOURNEY OVERVIEW:
{learning_context}

CURRENT PROGRESS:
{progress_context}

CONVERSATION GUIDELINES:

1. TONE & PERSONALITY
   - Be warm, encouraging, and genuinely interested
   - Use a conversational, friend-like tone
   - Celebrate achievements and progress
   - Provide gentle motivation during challenges
   - Be relatable and use appropriate humor when fitting

2. LEARNING SUPPORT
   - Ask thoughtful questions about learning goals
   - Suggest study techniques and best practices
   - Help break down overwhelming tasks
   - Provide perspective on learning challenges
   - Share relevant learning resources and tips

3. CAREER GUIDANCE
   - Offer insights about career paths and opportunities
   - Help with skill development planning
   - Suggest networking and professional development ideas
   - Provide industry context and trends
   - Connect current learning to future goals

4. PERSONAL DEVELOPMENT
   - Help with time management and productivity
   - Suggest work-life balance strategies
   - Encourage reflection on learning experiences
   - Support goal setting and milestone tracking
   - Foster growth mindset and resilience

WHEN USER DISCUSSES:
• Challenges → Provide empathy and practical solutions
• Achievements → Celebrate and encourage next steps
• Goals → Help refine and create action plans
• Career questions → Offer insights and guidance
• Learning struggles → Suggest strategies and perspective
• General topics → Engage naturally while connecting to growth

RESPONSE STYLE:
• Be conversational and natural
• Ask engaging follow-up questions
• Share relevant experiences or insights
• Provide actionable advice when appropriate
• Maintain positive, forward-looking perspective
• Remember details from previous conversations

Remember: You're not just an AI assistant, you're a learning companion who genuinely cares about the user's growth and success. Build rapport, show interest, and be the supportive mentor they need."""

    def analyze_conversation_context(self, message: str) -> Dict[str, Any]:
        """Analyze the message to determine appropriate conversation approach."""
        message_lower = message.lower()
        
        # Detect conversation type
        if any(word in message_lower for word in ['stuck', 'difficult', 'hard', 'frustrated', 'confused']):
            conversation_type = 'support_needed'
        elif any(word in message_lower for word in ['finished', 'completed', 'done', 'success', 'working']):
            conversation_type = 'celebration'
        elif any(word in message_lower for word in ['career', 'job', 'future', 'industry']):
            conversation_type = 'career_guidance'
        elif any(word in message_lower for word in ['goal', 'plan', 'next', 'should', 'want to learn']):
            conversation_type = 'goal_setting'
        else:
            conversation_type = 'general_chat'
        
        # Detect emotional tone
        emotional_indicators = {
            'excited': ['excited', 'awesome', 'great', 'amazing', 'love'],
            'frustrated': ['frustrated', 'annoying', 'hate', 'difficult', 'stuck'],
            'curious': ['why', 'how', 'what', 'interesting', 'learn more'],
            'uncertain': ['not sure', 'maybe', 'think', 'probably', 'confused']
        }
        
        detected_emotion = 'neutral'
        for emotion, indicators in emotional_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                detected_emotion = emotion
                break
        
        return {
            'conversation_type': conversation_type,
            'emotional_tone': detected_emotion,
            'needs_encouragement': detected_emotion in ['frustrated', 'uncertain'],
            'celebration_opportunity': detected_emotion == 'excited' or conversation_type == 'celebration'
        }
    
    def get_motivational_context(self) -> Dict[str, Any]:
        """Get context for providing appropriate motivation and encouragement."""
        user_interests = self.user_context.get('interests', [])
        career_path = self.user_context.get('career_path', '')
        skill_level = self.user_context.get('skill_level', 'beginner')
        
        # Motivation strategies based on user profile
        motivation_style = 'encouraging'  # Default
        
        if 'game' in ' '.join(user_interests).lower():
            motivation_style = 'achievement-oriented'
        elif career_path.lower() in ['entrepreneur', 'startup']:
            motivation_style = 'goal-driven'
        elif skill_level == 'beginner':
            motivation_style = 'supportive'
        
        return {
            'style': motivation_style,
            'interests': user_interests,
            'career_focus': career_path,
            'current_level': skill_level
        }
    
    def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message with chat/mentoring focus."""
        conversation_analysis = self.analyze_conversation_context(message)
        motivational_context = self.get_motivational_context()
        
        enhanced_context = {
            **context,
            'agent_mode': 'chat',
            'conversation_analysis': conversation_analysis,
            'motivational_context': motivational_context,
            'learning_progress': self.get_learning_progress_context(),
            'mentoring_mode': True,
            'system_prompt': self.get_system_prompt(),
            'agent_name': self.get_agent_name()
        }
        
        return enhanced_context 