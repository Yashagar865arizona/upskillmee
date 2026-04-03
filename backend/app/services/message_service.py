"""
Core service for handling chat message processing and AI responses.
Features:
- Message handling with context awareness
- Integration with OpenAI's GPT models
- Learning plan extraction
- Conversation handling
- Agent-based interaction system
"""

from typing import Dict, List, Any, Optional, Union, Tuple, cast
import logging
import json
import asyncio
import time
import re
import uuid
import threading
import numpy as np
from sqlalchemy.orm import Session
from openai import OpenAI
import openai
from datetime import datetime, timedelta,timezone

from app.models.project import Project
from ..config import settings
from ..models.user import User
from ..models.chat import Conversation, Message
from .ai_integration_service import AIIntegrationService
from .embedding_service import EmbeddingService
from .interest_extraction_service import InterestExtractionService
from .session_continuity_service import SessionContinuityService
from .session_service import SessionService
# Learning plan functionality now integrated into ai_integration_service
from ..agents import AgentManager, AgentMode

# Configure logger
logger = logging.getLogger(__name__)

class MessageService:
    def __init__(self, db: Session):
        """Initialize message service with component services"""
        self.db = db
        self.ai_service = AIIntegrationService()
        # Learning plan functionality now integrated into ai_integration_service
        self.embedding_service = self._initialize_embedding_service()
        self.interest_service = InterestExtractionService(db)
        self.current_conversation = None
        self.current_user = None
        self.agent_manager = None  # Will be initialized when user context is available

    def _initialize_embedding_service(self) -> Optional[EmbeddingService]:
        """Initialize embedding service with error handling"""
        try:
            logger.info("Initializing embedding service...")
            service = EmbeddingService(db=self.db)

            # Verify the service is properly initialized
            if service:
                logger.info(f"Successfully initialized embedding service with vector store type: {service}")
                logger.info(f"Embedding service store: {service.store.__class__.__name__}")
                return service
            else:
                logger.warning("Embedding service initialization returned None")
                return None
        except Exception as e:
            logger.error(f"Could not initialize embedding service: {str(e)}", exc_info=True)
            return None

    def set_current_user(self, user: User) -> None:
        """Set the current user"""
        self.current_user = user

    def set_current_conversation(self, conversation: Conversation) -> None:
        """Set the current conversation"""
        self.current_conversation = conversation

    def _detect_agent_mode(self, message: str, message_data: dict) -> AgentMode:
        """
        Detect the appropriate agent mode based on message content and context.
        
        Args:
            message: The user's message
            message_data: Full message data including any mode hints
            
        Returns:
            The appropriate AgentMode
        """
        # Check if mode is explicitly specified in message data
        explicit_mode = message_data.get('agent_mode')
        if explicit_mode:
            try:
                return AgentMode(explicit_mode)
            except ValueError:
                logger.warning(f"Invalid agent mode specified: {explicit_mode}")
        
        message_lower = message.lower()
        
        # Learning plan keywords - highest priority
        plan_keywords = [
            'create a learning plan', 'make a learning plan', 'build a learning plan',
            'learning plan', 'curriculum', 'roadmap', 'study plan', 'learning path',
            'create plan', 'new plan', 'edit plan', 'update plan'
        ]
        
        # Technical work keywords
        work_keywords = [
            'help with', 'how to implement', 'how to code', 'how to build',
            'debug', 'error', 'not working', 'step by step', 'tutorial',
            'code example', 'show me how', 'explain the code', 'fix this',
            'implement', 'create', 'build', 'make this work'
        ]
        
        # Chat/mentoring keywords
        chat_keywords = [
            'how are you', 'motivation', 'career advice', 'feeling',
            'what should i', 'advice', 'guidance', 'support',
            'encourage', 'help me understand', 'confused about',
            'struggling with', 'next steps'
        ]
        
        # Check for learning plan requests first (highest priority)
        if any(keyword in message_lower for keyword in plan_keywords):
            return AgentMode.PLAN
            
        # Check for technical work requests
        elif any(keyword in message_lower for keyword in work_keywords):
            return AgentMode.WORK
            
        # Check for chat/mentoring requests
        elif any(keyword in message_lower for keyword in chat_keywords):
            return AgentMode.CHAT
            
        # Default based on message characteristics
        else:
            # If message contains code or technical terms, use work mode
            if ('```' in message or 
                any(tech in message_lower for tech in ['function', 'class', 'variable', 'array', 'object', 'method'])):
                return AgentMode.WORK
                
            # If message is a question about learning or career, use chat mode
            elif (message.strip().endswith('?') and 
                  any(word in message_lower for word in ['learn', 'career', 'should', 'what', 'how', 'why'])):
                return AgentMode.CHAT
                
            # Default to chat mode for general conversation
            else:
                return AgentMode.CHAT

    def _initialize_agent_manager(self, user_context: Dict[str, Any]) -> None:
        """Initialize the agent manager with user context."""
        try:
            self.agent_manager = AgentManager(self.db, user_context)
            logger.info("Agent manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent manager: {str(e)}")
            self.agent_manager = None

    async def _run_async_operation(self, coroutine):
        """Helper method to run async operations in both sync and async contexts"""
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                return await coroutine
            else:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coroutine)
                    return future.result()
        except Exception as e:
            logger.error(f"Error running async operation: {str(e)}")
            return None

    async def _create_chat_history_summary(self, chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a concise summary of the chat history to improve memory, using embeddings for relevant context"""
        if not chat_history or len(chat_history) < 3:
            return {}

        try:
            if self.embedding_service and self.current_user and self.current_conversation:
                last_user_messages = [msg.get('text', '') for msg in chat_history[-5:]
                                     if msg.get('sender') == 'user' and msg.get('text')]

                if last_user_messages:
                    current_query = " ".join(last_user_messages)
                    query_embedding = await self._run_async_operation(
                        self.embedding_service.create_embedding(current_query)
                    )

                    if query_embedding is not None:
                        similar_messages = await self._run_async_operation(
                            self.embedding_service.search_similar_conversations(
                                db=self.db,
                                user_id=str(self.current_user.id),
                                query_embedding=query_embedding,
                                limit=5
                            )
                        )

                        if similar_messages:
                            logger.info(f"Found {len(similar_messages)} similar messages using RAG")
                            relevant_contexts = [
                                msg.get('content', '')
                                for msg in similar_messages
                                if (str(msg.get('conversation_id', '')) != str(self.current_conversation.id)
                                    and len(msg.get('content', '')) > 20)
                            ]

                            return {
                                "rag_contexts": relevant_contexts[:3],
                                "summary": self._create_traditional_summary(chat_history)
                            }

            return {"summary": self._create_traditional_summary(chat_history)}

        except Exception as e:
            logger.error(f"Error creating chat history summary: {str(e)}")
            return {}

    def _create_traditional_summary(self, chat_history: List[Dict[str, Any]]) -> str:
        """Create a traditional summary without using embeddings"""
        history_to_use = chat_history[-15:] if len(chat_history) > 15 else chat_history

        # Define keywords for analysis
        topic_keywords = {
            "programming", "machine learning", "data science", "AI", "artificial intelligence",
            "web development", "coding", "software", "math", "chemistry", "physics",
            "language", "business", "marketing", "finance", "art", "design", "music",
            "game development", "cybersecurity", "blockchain", "cryptocurrency", "nlp"
        }

        experience_keywords = {
            "beginner": {"beginner", "new to", "starting", "never done", "novice"},
            "intermediate": {"intermediate", "some experience", "familiar with"},
            "advanced": {"advanced", "expert", "professional", "years of experience", "good at"}
        }

        preference_keywords = {
            "hands-on": {"hands-on", "practical", "project", "building", "creating", "making"},
            "theoretical": {"theory", "concepts", "understanding", "reading", "books", "articles"},
            "visual": {"visual", "video", "watch", "see", "demonstration"}
        }

        # Initialize analysis results
        topics_mentioned = set()
        user_preferences = set()
        user_experience = None

        # Analyze messages
        for msg in history_to_use:
            if msg.get('sender') == 'user':
                text = msg.get('text', '').lower()

                # Extract topics
                topics_mentioned.update(topic for topic in topic_keywords if topic in text)

                # Extract experience level
                if not user_experience:
                    for level, keywords in experience_keywords.items():
                        if any(keyword in text for keyword in keywords):
                            user_experience = level
                            break

                # Extract preferences
                for pref, keywords in preference_keywords.items():
                    if any(keyword in text for keyword in keywords):
                        user_preferences.add(pref)

        # Build summary
        summary_parts = ["Previous conversation summary:"]

        if topics_mentioned:
            summary_parts.append(f"Topics discussed: {', '.join(topics_mentioned)}")

        if user_experience:
            summary_parts.append(f"User's experience level: {user_experience}")

        if user_preferences:
            summary_parts.append(f"Learning preferences: {', '.join(user_preferences)}")

        # Add recent messages
        summary_parts.append("\nMost recent exchanges:")
        for msg in history_to_use[-3:]:
            sender = "User" if msg.get('sender') == 'user' else "You"
            text = msg.get('text', '')
            summary_parts.append(f"{sender}: {text[:100]}{'...' if len(text) > 100 else ''}")

        return "\n".join(summary_parts)

    async def process_message(self, message_data: dict) -> Dict[str, Any]:
        """Process incoming message and generate response"""
        try:
            content = message_data.get('message', '')
            user_id = message_data.get('user_id')
            message_type = message_data.get('type')
            chat_history = message_data.get('chat_history', [])

            # Skip user_id check for auth and heartbeat messages
            if message_type not in ['auth', 'heartbeat']:
                # For all other messages, ensure user_id is provided
                if not user_id:
                    logger.warning("No user_id provided in message data")
                    return {
                        "text": "Authentication required. Please log in to continue.",
                        "sender": "bot",
                        "id": str(uuid.uuid4()),
                        "auth_required": True
                    }

            # Handle special message types
            if message_type in ['auth', 'heartbeat']:
                if message_type == 'heartbeat':
                    return {"status": "heartbeat_acknowledged", "type": "system"}
                return {"status": "acknowledged", "type": "system"}

            # For empty messages, return informative response
            if not content:
                return {
                    "text": "I'm here to help! Feel free to ask me a question or tell me what you'd like to learn.",
                    "sender": "bot",
                    "id": str(uuid.uuid4())
                }

            # Load conversation history from database if available
            current_conversation_id = None
            if self.current_conversation and self.db:
                current_conversation_id = str(self.current_conversation.id)
                try:
                    # OPTIMIZED: Get messages from database with proper indexing to prevent N+1 queries
                    # Use the optimized index: idx_messages_conversation_created_role
                    db_messages = self.db.query(Message).filter(
                        Message.conversation_id == self.current_conversation.id
                    ).order_by(Message.created_at.asc()).all()

                    # If db has more history than what was provided, use it
                    if len(db_messages) > len(chat_history):
                        logger.info(f"Using {len(db_messages)} messages from database for context")
                        chat_history = [
                            {
                                "sender": "user" if msg.role == "user" else "bot",
                                "text": msg.content,
                                "id": str(msg.id)
                            }
                            for msg in db_messages
                        ]
                except Exception as e:
                    logger.error(f"Error retrieving conversation history: {str(e)}")

            # Apply context window compression to avoid token overflows
            continuity_service = SessionContinuityService(self.db) if self.db else None
            if continuity_service and chat_history:
                chat_history = continuity_service.compress_messages_for_context(chat_history)

            # Get user information - try to load from database
            snapshot = {
                "user_context": {
                    "name": "",
                    "interests": [],
                    "career_path": "",
                    "skill_level": "beginner"
                }
            }

            # Load prior session context for returning users
            if continuity_service and user_id:
                prior_ctx = continuity_service.get_prior_session_context(
                    user_id=user_id,
                    current_conversation_id=current_conversation_id,
                )
                if prior_ctx.get("is_returning_user"):
                    snapshot["prior_session_context"] = prior_ctx
                    # Also inject into user_context so BaseAgent.get_base_context() can use it
                    snapshot["user_context"]["prior_session_context"] = prior_ctx
                    logger.info(
                        "SESSION_CONTINUITY: Returning user %s — injecting prior session context. Topics: %s",
                        user_id,
                        prior_ctx.get("last_session_topics", []),
                    )

            # Create chat history summary for memory enhancement - using RAG when possible
            chat_history_summary = await self._create_chat_history_summary(chat_history)
            if chat_history_summary:
                snapshot["chat_history_summary"] = chat_history_summary

            # Load user data for context
            if self.current_user:
                # Use current user data
                snapshot["user_context"]["name"] = getattr(self.current_user, "name", "")
                interests = getattr(self.current_user, "interests", [])
                if interests:
                    snapshot["user_context"]["interests"] = interests
                career_path = getattr(self.current_user, "career_path", "")
                if career_path:
                    snapshot["user_context"]["career_path"] = career_path
                skill_level = getattr(self.current_user, "skill_level", "beginner")
                if skill_level:
                    snapshot["user_context"]["skill_level"] = skill_level

                # Try to load existing learning plans for context
                try:
                    if self.db and user_id:
                        # Load directly from learning_plans table
                        from ..models.learning_plan import LearningPlan

                        # Get the most recent learning plan for this user
                        learning_plan = self.db.query(LearningPlan).filter(
                            LearningPlan.user_id == user_id
                        ).order_by(LearningPlan.created_at.desc()).first()

                        if learning_plan:
                            if "user_context" not in snapshot:
                                snapshot["user_context"] = {}

                            # Add the learning plan to the context
                            snapshot["user_context"]["learning_plans"] = [learning_plan.content]
                            logger.info(f"MEMORY: Loaded previous learning plan from database for context")
                            logger.info(f"MEMORY: Plan title: {learning_plan.title}")
                            logger.info(f"MEMORY: User ID used for query: {user_id}")
                            logger.info(f"MEMORY: Learning plan user_id: {learning_plan.user_id}")

                            # Log more details about the plan for debugging
                            plan = learning_plan.content
                            if 'projects' in plan and isinstance(plan['projects'], list):
                                logger.info(f"MEMORY: Plan has {len(plan['projects'])} projects")
                                for i, project in enumerate(plan['projects'][:2]):  # Log first 2 projects
                                    logger.info(f"MEMORY: Project {i+1}: {project.get('title', f'Project {i+1}')}")
                            
                            # Log the full context being passed to AI
                            logger.info(f"MEMORY: Full user context keys: {list(snapshot.get('user_context', {}).keys())}")
                        else:
                            logger.info(f"MEMORY: No learning plan found for user {user_id}")
                            
                            # Check if there are any learning plans in the database at all
                            all_plans = self.db.query(LearningPlan).all()
                            logger.info(f"MEMORY: Total learning plans in database: {len(all_plans)}")
                            if all_plans:
                                for plan in all_plans[:3]:  # Log first 3 plans
                                    logger.info(f"MEMORY: Found plan for user {plan.user_id}: {plan.title}")
                except Exception as e:
                    logger.error(f"Error loading learning plans: {str(e)}")
                    logger.error(f"Error details:", exc_info=True)

                # Load extracted interests from UserProfile and merge into context
                try:
                    extracted = self.interest_service.get_interests_as_strings(user_id)
                    if extracted:
                        existing = snapshot["user_context"].get("interests", [])
                        merged = list(dict.fromkeys(existing + extracted))
                        snapshot["user_context"]["interests"] = merged
                        logger.info(
                            "INTERESTS: Loaded %d extracted interests for user %s",
                            len(extracted),
                            user_id,
                        )
                    # Also load structured interest profile for richer agent context
                    structured_profile = self.interest_service.get_structured_profile(user_id)
                    if structured_profile:
                        snapshot["user_context"]["interest_profile"] = structured_profile
                except Exception as e:
                    logger.error("Error loading extracted interests: %s", e)

            # Format context with conversation history
            formatted_content = self._prepare_context_with_history(content, chat_history)

            # Detect learning plan requests
            # ONLY use hardcoded detection for learning plan requests
            direct_requests = [
                "create a learning plan",
                "make a learning plan",
                "build a learning plan",
                "i want a learning plan",
                "i need a learning plan",
                "can you create a learning plan",
                "could you make a learning plan",
                "create a new learning plan",
                "yes please create a learning plan",
                "create the learning plan again",
                "create the learning plan",
                "can u create the learning plan again",
                "can you create the learning plan again"
            ]

            # Avoid these ambiguous phrases that might trigger false positives
            ambiguous_phrases = [
                "create it again",
                "make it again",
                "create the plan again",
                "create a plan"
            ]

            # Log the exact content for debugging
            logger.info(f"Checking message for learning plan request: '{content}'")

            # Also check for "yes" responses after learning plan offers
            affirmative_responses = ["yes", "yes please", "sure", "ok", "okay"]

            # Check for direct requests - use exact phrase matching to avoid false positives
            direct_plan_request = any(request.lower() in content.lower() for request in direct_requests)

            # If we have a direct match from our explicit list, log it and proceed
            if direct_plan_request:
                logger.info(f"Direct learning plan request detected from phrase list: '{content}'")
            else:
                # Only check for ambiguous phrases if we don't have a direct match
                # Check for ambiguous phrases that might be false positives
                has_ambiguous_phrase = any(phrase.lower() in content.lower() for phrase in ambiguous_phrases)

                # If it's just an ambiguous phrase without a direct request, log it
                if has_ambiguous_phrase:
                    logger.warning(f"Ambiguous phrase detected but not a learning plan request: '{content}'")

            # Check if the previous message offered a learning plan
            offered_learning_plan = False
            if chat_history and len(chat_history) > 0:
                # Get the last bot message
                bot_messages = [msg for msg in chat_history if msg.get('sender') == 'bot']
                if bot_messages:
                    last_bot_message = bot_messages[-1]
                    last_bot_msg = last_bot_message.get('text', '').lower()
                    if ('learning plan' in last_bot_msg and
                        ('would you like' in last_bot_msg or
                         'want a learning plan' in last_bot_msg or
                         'like a learning plan' in last_bot_msg)):
                        offered_learning_plan = True
                        logger.info("Previous message offered a learning plan")

            # Check for affirmative response to an offer
            affirmative_to_offer = offered_learning_plan and content.lower().strip() in affirmative_responses

            # Consider it a plan request if it's a direct request OR an affirmative response to an offer
            is_plan_request = direct_plan_request or affirmative_to_offer

            # Log the decision with clear LEARNING_PLAN markers for easier log filtering
            if is_plan_request:
                logger.info(f"LEARNING_PLAN: Request detected - will generate plan")
            else:
                logger.info(f"LEARNING_PLAN: No request detected - normal conversation")

            # IMPORTANT: Make sure we don't accidentally trigger learning plan generation
            # for regular conversations
            if "special_instructions" not in snapshot:
                snapshot["special_instructions"] = {}
            snapshot["special_instructions"]["is_learning_plan_request"] = is_plan_request

            if direct_plan_request:
                logger.info("Direct learning plan request detected")
            elif affirmative_to_offer:
                logger.info("Affirmative response to learning plan offer detected")

            # Check if we have enough context for a good plan
            has_detailed_request = len(content.split()) > 15
            has_sufficient_history = len(chat_history) >= 3
            has_enough_context = has_detailed_request or has_sufficient_history

            # If learning plan requested but insufficient context, ask clarifying questions
            if is_plan_request and not has_enough_context:
                logger.info(f"Learning plan requested but insufficient context. Asking clarifying questions.")
                return {
                    "text": "I'd be happy to create a personalized learning plan for you! To make it truly tailored to your needs, could you tell me a bit more about:\n\n1. Your current skill level with this subject\n2. Why you're interested in learning it\n3. How you prefer to learn (hands-on projects, reading, videos, etc.)\n4. Any specific goals you have\n\nThis will help me create something that's perfect for you!",
                    "id": str(uuid.uuid4()),
                    "sender": "bot"
                }

            # Improved detection for topic requests vs learning plan requests
            # These are topics that users might mention without requesting a learning plan
            topic_keywords = ["programming", "machine learning", "data science", "AI", "artificial intelligence",
                            "web development", "coding", "software", "math", "chemistry", "physics",
                            "language", "business", "marketing", "finance", "art", "design", "music",
                            "game development", "cybersecurity", "blockchain", "cryptocurrency"]

            # First, detect if this is a simple topic mention (just the topic word with little context)
            is_simple_topic_mention = any(keyword in content.lower() for keyword in topic_keywords) and len(content.split()) < 5

            # Next, detect if this is a more detailed topic request but NOT a learning plan request
            is_topic_request = (any(keyword in content.lower() for keyword in topic_keywords)
                                and not is_plan_request
                                and len(content.split()) > 3)

            # If this is a topic request without a learning plan request, add special instructions
            if (is_simple_topic_mention or is_topic_request) and not is_plan_request:
                logger.info(f"Detected topic mention without plan request. Adding exploration instructions.")

                # Add a special reminder to the snapshot to ensure GPT acts as a mentor
                if "special_instructions" not in snapshot:
                    snapshot["special_instructions"] = {}

                # Get the list of matched topics
                matched_topics = [kw for kw in topic_keywords if kw in content.lower()]
                topics_str = ", ".join(matched_topics) if matched_topics else "this topic"

                if is_simple_topic_mention:
                    # For very simple mentions like just "machine learning"
                    snapshot["special_instructions"]["topic_exploration"] = (
                        f"IMPORTANT: The user has mentioned a topic ({topics_str}) "
                        "with very little context. This is a perfect opportunity to be a mentor. "
                        "1. Respond with enthusiastic but brief acknowledgement of the topic "
                        "2. Ask 2-3 engaging questions to understand their interest level, experience, and goals "
                        "3. Use a casual, friendly tone with a touch of humor "
                        "4. DO NOT create a learning plan or structured steps - just have a conversation "
                        "5. Keep your response under 5 sentences total"
                    )
                else:
                    # For more detailed topic requests
                    snapshot["special_instructions"]["topic_exploration"] = (
                        f"IMPORTANT: The user is asking about {topics_str}. "
                        "Act as an engaging mentor by: "
                        "1. Responding with 1-2 interesting facts about the topic that might surprise them "
                        "2. Asking about their specific interests within this area "
                        "3. Using a conversational, casual tone with occasional humor "
                        "4. Finding out what their learning style is "
                        "5. DO NOT create a learning plan or list steps - that's not your role"
                    )

            # Initialize agent manager if not already done
            if not self.agent_manager:
                self._initialize_agent_manager(snapshot.get("user_context", {}))

            # Detect appropriate agent mode
            agent_mode = self._detect_agent_mode(content, message_data)
            logger.info(f"Detected agent mode: {agent_mode.value}")

            # Get AI response based on request type using agent system
            logger.info("Getting AI response using agent system")
            start_time = time.time()

            # Variable to store the final response
            response_text = ""
            response_metadata = None

            # Use agent system to enhance context and get appropriate system prompt
            if self.agent_manager:
                try:
                    # Process message through agent system
                    enhanced_context = self.agent_manager.process_message(
                        message=content,
                        mode=agent_mode,
                        context=snapshot
                    )
                    
                    # Update snapshot with agent-enhanced context
                    snapshot.update(enhanced_context)
                    
                    logger.info(f"Agent system enhanced context with {agent_mode.value} mode")
                    logger.info(f"System prompt length: {len(enhanced_context.get('system_prompt', ''))}")
                    
                except Exception as e:
                    logger.error(f"Error in agent system processing: {str(e)}")
                    # Continue with original snapshot if agent processing fails

            # IMPORTANT: For learning plan requests, use DeepSeek directly and don't let GPT generate plans
            if is_plan_request or agent_mode == AgentMode.PLAN:
                logger.info("Learning plan requested - using DeepSeek")
                # This immediate response would be sent via websocket in a real implementation
                # We log it here for reference but don't actually send it in this implementation
                logger.info("Would send interim message: I'm creating a personalized learning journey for you. This might take a moment as I'm designing something special just for you!")

                # Let AI integration service handle it - it will use DeepSeek for plans
                # Pass is_plan_request=True to ensure it uses the learning plan generation path
                response_text, response_metadata = await self.ai_service.get_ai_response(formatted_content, snapshot, is_plan_request=True)

                # Process learning plan from response
                if response_metadata and 'learning_plan' in response_metadata and user_id:
                    # Log the learning plan data for debugging
                    logger.info(f"Learning plan generated successfully: {response_metadata['learning_plan'].get('title', 'Untitled')}")
                    logger.info(f"Plan structure: {', '.join(response_metadata['learning_plan'].keys())}")

                    # Log the full learning plan content
                    logger.info("===== FULL LEARNING PLAN CONTENT (MESSAGE SERVICE) =====")
                    logger.info(f"Full plan JSON: {json.dumps(response_metadata['learning_plan'], indent=2)}")
                    logger.info("===== END LEARNING PLAN CONTENT ====")

                    # Save learning plan to database
                    # We'll use a synchronous version for now
                    plan_id = self._save_learning_plan_to_db_sync(user_id, response_metadata["learning_plan"])
                    logger.info(f"Saved learning plan with ID: {plan_id}")

                    # Save this message to database for future context
                    if self.current_conversation and self.db:
                        try:
                            # Create a Message object directly or with dict unpacking to avoid linter issues
                            message_data = {
                                "user_id": user_id,
                                "conversation_id": self.current_conversation.id,
                                "content": response_text,
                                "role": "assistant",
                                "message_metadata": {"learning_plan": response_metadata["learning_plan"]}
                            }
                            new_message = Message(**message_data)
                            self.db.add(new_message)
                            self.db.commit()
                            logger.info(f"Saved learning plan message to database")

                            # Store embeddings for vector search
                            try:
                                # Save message embedding
                                if self.embedding_service and content and response_text and user_id:
                                    # Process embeddings in background
                                    conversation_id_int = int(str(self.current_conversation.id))
                                    self._store_embeddings(
                                        user_id=user_id,
                                        content=content,
                                        response_text=response_text,
                                        conversation_id=conversation_id_int
                                    )
                            except Exception as e:
                                logger.error(f"Error storing embeddings: {str(e)}")

                        except Exception as e:
                            logger.error(f"Error saving message: {str(e)}")
                            # Continue execution even if database save fails

                    # Generate learning plan URL if user_id is available
                    project_id = None
                    if user_id and plan_id:
                        logger.info(f"Creating project from learning plan for frontend display")
                        project_id = self._create_project_from_learning_plan(user_id, response_metadata["learning_plan"], plan_id)
                        logger.info(f"Project created with ID: {project_id}")

                    # Return redirect message instead of the actual learning plan
                    logger.info(f"LEARNING_PLAN_DISPLAY: Sending learning plan redirect to frontend for project {project_id}")
                    response_data = {
                        "text": f"Great news! I've created a personalized learning plan for you based on our conversation. You can view it on your project board now.\n\nI've organized everything into achievable milestones with fun challenges and practical skills. Head over to your projects page to check it out!",
                        "project_redirect": True,
                        "project_id": project_id,
                        "id": str(uuid.uuid4()),
                        "sender": "bot",
                        "learning_plan": response_metadata["learning_plan"]
                    }
                    logger.info(f"LEARNING_PLAN_STRUCTURE: Sending response with keys: {', '.join(response_data.keys())}")
                    return response_data
                else:
                    # If no plan in metadata, try to extract from response
                    plan_data = self._extract_learning_plan(response_text)
                    if plan_data and user_id:
                        # Save to database
                        # We'll use a synchronous version for now
                        plan_id = self._save_learning_plan_to_db_sync(user_id, plan_data)
                        logger.info(f"Saved learning plan with ID: {plan_id}")

                        # Save this message to database
                        if self.current_conversation and self.db:
                            try:
                                # Create a Message object with dict unpacking
                                message_data = {
                                    "user_id": user_id,
                                    "conversation_id": self.current_conversation.id,
                                    "content": response_text,
                                    "role": "assistant",
                                    "message_metadata": {"learning_plan": plan_data}
                                }
                                new_message = Message(**message_data)
                                self.db.add(new_message)
                                self.db.commit()
                                logger.info(f"Saved extracted learning plan message to database")

                                # Store embeddings for vector search
                                try:
                                    # Save message embedding
                                    if self.embedding_service and content and response_text and user_id:
                                        # Process embeddings in background
                                        conversation_id_int = int(str(self.current_conversation.id))
                                        self._store_embeddings(
                                            user_id=user_id,
                                            content=content,
                                            response_text=response_text,
                                            conversation_id=conversation_id_int
                                        )
                                except Exception as e:
                                    logger.error(f"Error storing embeddings: {str(e)}")

                            except Exception as e:
                                logger.error(f"Error saving message: {str(e)}")
                                # Continue execution even if database save fails

                        # Generate learning plan URL if user_id is available
                        project_id = None
                        if user_id:
                            logger.info(f"Creating project from extracted learning plan for frontend display")
                            project_id = self._create_project_from_learning_plan(user_id, plan_data)
                            logger.info(f"Project created with ID: {project_id}")

                        # Return redirect message instead of the actual learning plan
                        logger.info(f"LEARNING_PLAN_DISPLAY: Sending learning plan redirect to frontend for project {project_id}")
                        response_data = {
                            "text": f"Great news! I've created a personalized learning plan for you based on our conversation. You can view it on your project board now.\n\nI've organized everything into achievable milestones with fun challenges and practical skills. Head over to your projects page to check it out!",
                            "project_redirect": True,
                            "project_id": project_id,
                            "id": str(uuid.uuid4()),
                            "sender": "bot",
                            "learning_plan": plan_data
                        }
                        logger.info(f"LEARNING_PLAN_STRUCTURE: Sending response with keys: {', '.join(response_data.keys())}")
                        return response_data

                # If no plan was found but a plan was requested, return a basic response
                logger.warning("Learning plan requested but no plan found in response")
                return {
                    "text": response_text or "I tried to create a learning plan, but encountered an issue. Could you provide more specific details about what you'd like to learn?",
                    "id": str(uuid.uuid4()),
                    "sender": "bot"
                }
            else:
                # For regular conversations, use agent-enhanced context
                logger.info(f"Regular conversation - using {agent_mode.value} agent mode")
                response_text, response_metadata = await self.ai_service.get_ai_response(formatted_content, snapshot)

            logger.info(f"AI response received in {time.time() - start_time:.2f} seconds")

            # Save regular message to database for context persistence
            if self.current_conversation and self.db:
                try:
                    # Save user and bot messages
                    try:
                        # Session instrumentation — get or create active session
                        session_svc = SessionService(self.db)
                        active_session = session_svc.get_or_create_session(user_id)
                        session_id = active_session.id

                        # User message
                        user_msg_data = {
                            "user_id": user_id,
                            "conversation_id": self.current_conversation.id,
                            "session_id": session_id,
                            "content": content,
                            "role": "user",
                            "message_metadata": {}
                        }
                        user_message = Message(**user_msg_data)
                        self.db.add(user_message)

                        # Bot response
                        bot_msg_data = {
                            "user_id": user_id,
                            "conversation_id": self.current_conversation.id,
                            "session_id": session_id,
                            "content": response_text,
                            "role": "assistant",
                            "message_metadata": response_metadata if response_metadata else {}
                        }
                        bot_message = Message(**bot_msg_data)
                        self.db.add(bot_message)

                        # Increment session message count (1 user turn = 1 exchange)
                        session_svc.record_message(session_id)

                        # Commit to database so we have valid IDs
                        self.db.commit()
                        logger.info("Saved conversation messages to database")

                        # Extract and persist interest signals from the user message
                        if user_id and content:
                            asyncio.create_task(
                                self.interest_service.extract_and_store(user_id, content)
                            )

                        # Store embeddings for vector search
                        try:
                            # Save message embedding
                            if self.embedding_service and content and response_text:
                                # Process embeddings in background if user_id is available
                                if user_id:
                                    conversation_id_int = int(str(self.current_conversation.id))
                                    self._store_embeddings(
                                        user_id=user_id,
                                        content=content,
                                        response_text=response_text,
                                        conversation_id=conversation_id_int
                                    )
                        except Exception as e:
                            logger.error(f"Error storing embeddings: {str(e)}")

                    except Exception as db_error:
                        logger.error(f"Database error: {str(db_error)}")
                        self.db.rollback()  # Rollback transaction on error
                except Exception as e:
                    logger.error(f"Outer error in message saving: {str(e)}")

            # Return standard response with agent information
            # Suggest a mode switch
            suggested_mode = None
            if self.agent_manager and 'agent_mode' in locals():
                suggested_mode_enum = self.agent_manager.suggest_mode_switch(content, agent_mode)
                if suggested_mode_enum:
                    suggested_mode = suggested_mode_enum.value
            response_data = {
                "text": response_text or "I apologize, I couldn't generate a response. Please try again.",
                "id": str(uuid.uuid4()),
                "sender": "bot",
                "agent_mode": agent_mode.value if 'agent_mode' in locals() else 'chat',
                "suggested_mode": suggested_mode
            }
            
            # Add agent metadata if available
            if self.agent_manager and 'agent_mode' in locals():
                response_data["agent_info"] = {
                    "mode": agent_mode.value,
                    "agent_name": snapshot.get('agent_name', 'Unknown'),
                    "available_modes": self.agent_manager.get_available_modes()
                }
            
            return response_data

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {"text": f"An error occurred while processing your message. Please try again.", "sender": "bot", "id": str(uuid.uuid4())}

    def _prepare_context_with_history(self, content: str, chat_history: List[Dict[str, Any]]) -> str:
        """Prepare user message with chat history context"""
        # For simple greetings, don't include history
        simple_greetings = ["hi", "hello", "hey", "hi there", "hello there", "good morning", "good afternoon", "good evening"]
        if content.lower().strip() in simple_greetings:
            return content

        # If chat history is empty or very short, just return the content
        if not chat_history or len(chat_history) < 2:
            return content

        # Limit history to the last 3 messages for efficiency
        recent_history = chat_history[-3:]

        # Format minimal context
        context = ""
        for msg in recent_history:
            role = "User" if msg.get('sender', '') == 'user' else "Assistant"
            text = msg.get('text', '').strip()
            if text:
                if len(text) > 100:
                    text = text[:97] + "..."
                context += f"{role}: {text}\n\n"

        # Add the current message
        context += f"User: {content}"
        return context

    def _extract_learning_plan(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract a learning plan from message content"""
        try:
            # Use the learning plan service's methods for consistency
            # First try to find JSON blocks in code fences
            json_blocks = re.findall(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
            if json_blocks:
                for block in json_blocks:
                    try:
                        data = json.loads(block)
                        if isinstance(data, dict):
                            # Extract plan data directly
                            plan_data = self.learning_plan_service.extract_learning_plan(text)
                            if plan_data:
                                logger.info(f"Successfully extracted learning plan from JSON block with {len(plan_data.get('projects', []))} projects")
                                return plan_data
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON block: {str(e)}")
                        continue

            # If no JSON in code fences, try to find raw JSON
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    if isinstance(data, dict):
                        # Extract plan data directly
                        plan_data = self.learning_plan_service.extract_learning_plan(text)
                        if plan_data:
                            logger.info(f"Successfully extracted learning plan from raw JSON with {len(plan_data.get('projects', []))} projects")
                            return plan_data
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse raw JSON: {str(e)}")

            # If no valid JSON found, try to extract a structured plan from the text
            structured_plan = self.learning_plan_service.create_structured_plan_from_text(text)
            if structured_plan:
                logger.info(f"Created structured plan from text with {len(structured_plan.get('projects', []))} projects")
                return structured_plan

            return None

        except Exception as e:
            logger.error(f"Error extracting learning plan: {str(e)}")
            return None

    def _save_learning_plan_to_db_sync(self, user_id: str, plan_data: Dict[str, Any]) -> Optional[str]:
        """Save learning plan to database and vector store for future reference

        Args:
            user_id: The user ID to save the plan for
            plan_data: The learning plan data

        Returns:
            The ID of the created learning plan, or None if failed
        """
        try:
            # Log the plan data for debugging
            logger.info(f"Attempting to save learning plan: {plan_data.get('title', 'Untitled')}")
            logger.info(f"Plan has {len(plan_data.get('projects', []))} projects")

            if not self.db:
                logger.warning("Can't save learning plan: missing db connection")
                return None

            # Log user info
            logger.info(f"Saving learning plan for user {user_id}")

            # Find the user
            from ..models.user import User
            from ..models.learning_plan import LearningPlan

            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"User {user_id} not found, can't save learning plan")
                return None

            # 1. Save to the dedicated LearningPlan table
            try:
                # Create a new LearningPlan object
                from ..models.learning_plan import LearningPlan

                # Extract title and description
                title = plan_data.get('title', 'Untitled Learning Plan')
                description = plan_data.get('description', '')

                # Create the learning plan record
                learning_plan = LearningPlan()
                setattr(learning_plan, 'user_id', user_id)
                setattr(learning_plan, 'title', title)
                setattr(learning_plan, 'description', description)
                setattr(learning_plan, 'content', plan_data)

                # Save to database
                self.db.add(learning_plan)
                self.db.flush()  # Get the ID without committing yet

                logger.info(f"Created learning plan record with ID: {learning_plan.id}")

                # No longer saving to user metadata since it doesn't exist
                # Instead, we'll rely on the dedicated LearningPlan table
                logger.info(f"Learning plan saved to dedicated table with ID: {learning_plan.id}")

                # 3. Store in vector database for RAG retrieval - skip for now
                # We'll implement this in a separate PR to avoid scope creep
                logger.info("Vector storage for learning plans will be implemented in a future update")

                # Commit all changes
                self.db.commit()
                logger.info(f"Successfully saved learning plan to database and user metadata")

                # Return the learning plan ID
                return str(learning_plan.id)

            except Exception as e:
                logger.error(f"Error saving learning plan to database: {str(e)}")
                self.db.rollback()
                return None


        except Exception as e:
            logger.error(f"Error in learning plan save: {str(e)}", exc_info=True)
            return None

    def _format_learning_plan_text(self, plan_data: Dict[str, Any]) -> str:
        """Format a learning plan as text for embedding

        Args:
            plan_data: The learning plan data

        Returns:
            A text representation of the learning plan
        """
        text_parts = []

        # Add title and description
        text_parts.append(f"Learning Plan: {plan_data.get('title', 'Untitled')}")
        text_parts.append(f"Description: {plan_data.get('description', '')}")

        # Add projects
        if 'projects' in plan_data and isinstance(plan_data['projects'], list):
            for i, project in enumerate(plan_data['projects']):
                text_parts.append(f"\nProject {i+1}: {project.get('title', f'Project {i+1}')}")
                text_parts.append(f"Project Description: {project.get('description', '')}")

                # Add tasks
                if 'tasks' in project and isinstance(project['tasks'], list):
                    text_parts.append("Tasks:")
                    for task in project['tasks']:
                        text_parts.append(f"- {task}")

                # Add skills
                if 'skills' in project and isinstance(project['skills'], list):
                    text_parts.append("Skills:")
                    for skill in project['skills']:
                        text_parts.append(f"- {skill}")

                # Add resources
                if 'resources' in project and isinstance(project['resources'], list):
                    text_parts.append("Resources:")
                    for resource in project['resources']:
                        text_parts.append(f"- {resource}")

                # Add weeks/duration
                if 'weeks' in project:
                    text_parts.append(f"Duration: {project['weeks']}")
                elif 'duration' in project:
                    text_parts.append(f"Duration: {project['duration']}")

        return "\n".join(text_parts)

    def _store_embeddings(self, user_id: str, content: str, response_text: str, conversation_id: int):
        """Store embeddings for user message and bot response in the vector database"""
        if not self.embedding_service:
            logger.warning("Embedding service not available, skipping embedding storage")
            return

        try:
            # Run in a separate thread to avoid blocking
            import threading

            def create_and_store_embeddings():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    # Only proceed if embedding service is available
                    if self.embedding_service:
                        logger.info(f"Creating embedding for user message: '{content[:50]}...'" )

                        # Create embedding for user message
                        user_embedding = None
                        try:
                            user_embedding = loop.run_until_complete(
                                self.embedding_service.create_embedding(content)
                            )
                            logger.info(f"Successfully created user message embedding with dimension: {len(user_embedding) if user_embedding is not None else 'None'}")
                        except Exception as e:
                            logger.error(f"Failed to create user message embedding: {str(e)}")

                        # Store in vector database
                        if user_embedding is not None and self.embedding_service:
                            # Only store if user_id is provided
                            if user_id:
                                try:
                                    logger.info(f"Storing user message embedding in vector database for user {user_id}")
                                    loop.run_until_complete(
                                        self.embedding_service.store_conversation(
                                            db=self.db,
                                            user_id=str(user_id),
                                            text=content,
                                            embedding=user_embedding,
                                            conversation_id=conversation_id,
                                            role="user"
                                        )
                                    )
                                    logger.info("Successfully stored user message embedding in vector database")
                                except Exception as e:
                                    logger.error(f"Failed to store user message embedding: {str(e)}")
                            else:
                                logger.warning("No user_id provided, skipping user message embedding storage")

                        # Create embedding for bot response
                        if self.embedding_service:
                            logger.info(f"Creating embedding for bot response: '{response_text[:50]}'" )

                            bot_embedding = None
                            try:
                                bot_embedding = loop.run_until_complete(
                                    self.embedding_service.create_embedding(response_text)
                                )
                                logger.info(f"Successfully created bot response embedding with dimension: {len(bot_embedding) if bot_embedding is not None else 'None'}")
                            except Exception as e:
                                logger.error(f"Failed to create bot response embedding: {str(e)}")

                            # Store in vector database
                            if bot_embedding is not None and self.embedding_service:
                                # Only store if user_id is provided
                                if user_id:
                                    try:
                                        logger.info(f"Storing bot response embedding in vector database for user {user_id}")
                                        loop.run_until_complete(
                                            self.embedding_service.store_conversation(
                                                db=self.db,
                                                user_id=str(user_id),
                                                text=response_text,
                                                embedding=bot_embedding,
                                                conversation_id=conversation_id,
                                                role="assistant"
                                            )
                                        )
                                        logger.info("Successfully stored bot response embedding in vector database")
                                    except Exception as e:
                                        logger.error(f"Failed to store bot response embedding: {str(e)}")
                                else:
                                    logger.warning("No user_id provided, skipping bot response embedding storage")
                except Exception as e:
                    logger.error(f"Error in embedding creation/storage process: {str(e)}")
                finally:
                    loop.close()

            # Start the embedding process in background
            thread = threading.Thread(target=create_and_store_embeddings)
            thread.daemon = True  # Make thread a daemon so it doesn't block program exit
            thread.start()
            logger.info(f"Started background thread for embedding storage with thread ID: {thread.ident}")
        except Exception as e:
            logger.error(f"Failed to start embedding thread: {str(e)}")


   
    def _create_project_from_learning_plan(
    self, user_id: str, plan_data: Dict[str, Any], learning_plan_id: str
) -> str:
     """
     Create projects from a learning plan and store them in the database.
     Dynamically divides the plan duration across projects and distributes tasks.
     """
     try:
        logger.info("===== PROJECT CREATION FROM LEARNING PLAN =====")

        from ..models.project import Project, ProjectPhase, Task, Milestone

        projects_only = plan_data.get("projects", [])
        if not projects_only:
            return "error-no-projects"

       
        plan_start_date_str = plan_data.get("start_date")
        plan_start_date = (
            datetime.fromisoformat(plan_start_date_str).replace(tzinfo=timezone.utc)
            if plan_start_date_str else datetime.now(timezone.utc)
        )

        
        total_weeks = plan_data.get("duration_weeks", 4)
        plan_end_date = plan_start_date + timedelta(weeks=total_weeks)

        num_projects = len(projects_only)
        if num_projects == 0:
            return "error-no-projects"

        
        days_per_project = (plan_end_date - plan_start_date).days // num_projects

        last_project_id = None
        current_start = plan_start_date

        for i, project_item in enumerate(projects_only):
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
                project_metadata=project_item,
            )
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            last_project_id = str(project.id)

           
            tasks = project_item.get("tasks", [])
            total_tasks = len(tasks)
            for j, task_desc in enumerate(tasks):
                if isinstance(task_desc, str):
                    task_title, task_description = f"Task {i+1}.{j+1}", task_desc
                elif isinstance(task_desc, dict):
                    task_title = task_desc.get("title", f"Task {i+1}.{j+1}")
                    task_description = task_desc.get("description", "")
                else:
                    continue

                task_deadline = None
                if total_tasks > 0:
                    total_seconds = (project_end - current_start).total_seconds()
                    seconds_per_task = total_seconds / total_tasks
                    task_deadline = current_start + timedelta(seconds=seconds_per_task * (j + 1))

                task = Task(
                    project_id=project.id,
                    title=task_title,
                    description=task_description,
                    status="pending",
                    priority="medium",
                    due_date=task_deadline,
                )
                self.db.add(task)
                self.db.commit()

           
            milestone = Milestone(
                project_id=project.id,
                title=project_name,
                description=project_description,
                target_date=project_end,
            )
            self.db.add(milestone)
            self.db.commit()

            
            current_start = project_end + timedelta(days=1)

        return last_project_id

     except Exception as e:
        logger.error(f"Failed to create projects from learning plan: {str(e)}")
        self.db.rollback()
        return "error-project-creation-failed"


    def _create_milestones_from_plan(self, project: Project, project_data: Dict[str, Any]) -> None:
     """Create milestones and tasks for a specific project"""
     from ..models.project import Milestone, Task

     logger.info(f"===== Creating milestones for project {project.id}: {project.title} =====")
 
     
     weeks_per_milestone = 2
     phases = ["Planning", "Execution", "Review"]

     for i, phase in enumerate(phases):
        milestone = Milestone(
            project_id=project.id,
            title=f"{phase} Phase",
            description=project_data.get("description", ""),
            target_date=datetime.utcnow() + timedelta(weeks=(i+1) * weeks_per_milestone)
        )
        self.db.add(milestone)

     
     for task_data in project_data.get("tasks", []):
        task = Task(
            project_id=project.id,
            title=task_data.get("title", "Untitled Task"),
            description=task_data.get("description", ""),
            status=task_data.get("status", "pending"),
            priority=task_data.get("priority", "medium"),
            due_date=datetime.utcnow() + timedelta(weeks=1) 
        )
        self.db.add(task)

     self.db.commit()
