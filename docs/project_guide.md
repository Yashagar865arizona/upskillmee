# Ponder - AI Learning Platform Guide

## Project Context for AI Assistants

This is a comprehensive guide for AI assistants working on the Ponder project. Read this document carefully to understand the project's scope, requirements, and implementation details.

### Important Notes for AI Assistants

1. **Frontend Design Policy**
   - DO NOT modify existing frontend components or design
   - Preserve current UI/UX patterns and color schemes
   - All frontend changes must be explicitly approved
   - Focus on backend logic and AI integration

2. **Response Guidelines**
   - Keep responses concise and focused
   - Provide code examples when relevant
   - Follow existing patterns and conventions
   - Prioritize user experience and learning effectiveness

3. **Project Understanding**
   - This is an AI-powered learning platform
   - Uses conversational interface for education
   - Focuses on personalized learning paths
   - Maintains context across sessions

## System Architecture

### Frontend Architecture (DO NOT MODIFY)

1. **Core Components**
   ```jsx
   // Main Chat Interface
   <ChatContainer>
     <MessageList>  // Displays chat history
     <UserInput />  // Message input with suggestions
     <ContextPanel />  // Shows learning resources
   </ChatContainer>

   // Learning Dashboard
   <DashboardContainer>
     <ProgressSection />  // Shows learning progress
     <LearningPathView /> // Current learning path
     <RecommendationsPanel />  // Next topics
   </DashboardContainer>
   ```

2. **State Management**
   ```javascript
   // Redux Store Structure
   {
     chat: {
       messages: [],
       context: {},
       isTyping: boolean
     },
     learning: {
       currentPath: {},
       progress: {},
       recommendations: []
     },
     user: {
       preferences: {},
       profile: {},
       settings: {}
     }
   }
   ```

### Backend Architecture

1. **Core Services**
   ```python
   # Message Service
   class MessageService:
       async def process_message(self, message: str, context: Dict) -> Response:
           intent = await self.analyze_intent(message)
           learning_context = await self.get_learning_context(intent)
           response = await self.generate_response(message, intent, learning_context)
           await self.update_learning_progress(intent, response)
           return response

   # Learning Service
   class LearningService:
       async def create_learning_path(self, user_profile: Dict) -> LearningPath:
           goals = self.analyze_goals(user_profile)
           path = self.generate_path(goals)
           return self.add_checkpoints(path)

   # Onboarding Service
   class OnboardingService:
       async def process_onboarding(self, user_data: Dict) -> UserProfile:
           profile = self.create_profile(user_data)
           initial_path = await self.learning_service.create_learning_path(profile)
           return profile, initial_path
   ```

2. **Database Models**
   ```python
   # User Profile
   class UserProfile(BaseModel):
       id: str
       learning_style: str
       pace: str
       interests: List[str]
       current_level: Dict[str, int]
       goals: List[str]

   # Learning Path
   class LearningPath(BaseModel):
       id: str
       user_id: str
       topics: List[Topic]
       progress: float
       checkpoints: List[Checkpoint]

   # Message
   class Message(BaseModel):
       id: str
       user_id: str
       content: str
       context: Dict[str, Any]
       timestamp: datetime
   ```

3. **API Endpoints**
   ```python
   # Chat Router
   @router.websocket("/ws")
   async def chat_websocket(websocket: WebSocket):
       await handle_websocket_connection(websocket)

   @router.post("/chat")
   async def process_message(message: MessageRequest):
       return await message_service.process(message)

   # Learning Router
   @router.post("/learning-path")
   async def create_path(request: PathRequest):
       return await learning_service.create_path(request)

   @router.get("/progress")
   async def get_progress(user_id: str):
       return await learning_service.get_progress(user_id)
   ```

### AI Integration Points

1. **Message Processing**
   ```python
   async def process_message(message: str) -> Response:
       # 1. Intent Analysis
       intent = analyze_intent(message)
       
       # 2. Context Retrieval
       context = {
           'learning_path': current_path,
           'progress': user_progress,
           'recent_topics': recent_topics,
           'mistakes': recent_mistakes
       }
       
       # 3. Response Generation
       response = generate_response(message, intent, context)
       
       # 4. Progress Update
       update_progress(intent, response)
       
       return response
   ```

2. **Learning Path Generation**
   ```python
   async def generate_learning_path(profile: UserProfile) -> LearningPath:
       # 1. Goal Analysis
       goals = analyze_goals(profile.goals)
       
       # 2. Topic Mapping
       topics = map_topics_to_goals(goals)
       
       # 3. Difficulty Adjustment
       adjusted_topics = adjust_difficulty(topics, profile.current_level)
       
       # 4. Checkpoint Creation
       path_with_checkpoints = add_checkpoints(adjusted_topics)
       
       return path_with_checkpoints
   ```

## Implementation Guidelines

### AI Behavior Rules

1. **Response Generation**
   - Use Socratic method (guide through questions)
   - Adapt complexity to user level
   - Maintain conversation context
   - Include practical examples
   - Keep responses focused and relevant

2. **Learning Assessment**
   - Regular comprehension checks
   - Gradual difficulty progression
   - Identify knowledge gaps
   - Provide constructive feedback
   - Track learning velocity

3. **Error Recovery**
   - Graceful error handling
   - Clear error messages
   - Automatic retries when appropriate
   - Maintain conversation flow
   - Save progress frequently

### Code Style Guide

1. **Python Backend**
   ```python
   # Use type hints
   def process_message(message: str, context: Dict[str, Any]) -> Response:
       pass

   # Use async/await
   async def handle_request(request: Request) -> Response:
       pass

   # Use dependency injection
   def get_service(db: Session = Depends(get_db)) -> Service:
       pass
   ```

2. **Database Operations**
   ```python
   # Use SQLAlchemy models
   class User(Base):
       __tablename__ = "users"
       id = Column(String, primary_key=True)
       profile = Column(JSON)

   # Use async operations
   async def get_user(user_id: str) -> User:
       async with Session() as session:
           return await session.get(User, user_id)
   ```

## Testing Requirements

1. **Backend Tests**
   ```python
   # Service Tests
   async def test_message_processing():
       response = await message_service.process(test_message)
       assert response.status == 200
       assert response.content is not None

   # API Tests
   async def test_chat_endpoint():
       response = await client.post("/chat", json=test_data)
       assert response.status_code == 200
   ```

2. **Integration Tests**
   ```python
   # WebSocket Tests
   async def test_websocket():
       async with websocket_connect("/ws") as ws:
           await ws.send_json(test_message)
           response = await ws.receive_json()
           assert response['status'] == 'success'
   ```

## Monitoring and Analytics

1. **Performance Metrics**
   ```python
   # Latency Tracking
   @metrics.track_latency("message_processing")
   async def process_message():
       pass

   # Error Tracking
   @metrics.track_errors("api_errors")
   async def api_endpoint():
       pass
   ```

2. **Learning Metrics**
   ```python
   # Progress Tracking
   @metrics.track_progress
   async def update_progress():
       pass

   # Engagement Tracking
   @metrics.track_engagement
   async def handle_interaction():
       pass
   ```

## Development Process

1. **Feature Implementation**
   - Create feature branch
   - Implement backend changes
   - Add tests
   - Update documentation
   - Create PR for review

2. **Deployment Steps**
   - Run test suite
   - Update dependencies
   - Run migrations
   - Deploy to staging
   - Monitor metrics

## Important Reminders

1. **DO NOT**
   - Modify frontend design
   - Change existing UI patterns
   - Alter response formats
   - Break type contracts

2. **DO**
   - Follow existing patterns
   - Add comprehensive tests
   - Document changes
   - Monitor performance
   - Maintain code quality

## Conclusion

This document serves as the single source of truth for AI assistants working on the Ponder project. Follow these guidelines carefully to maintain consistency and quality in the codebase.
