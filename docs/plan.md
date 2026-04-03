# Ponder System Architecture

## 1. System Overview

Ponder is an AI-powered learning assistant that uses RAG (Retrieval Augmented Generation) for personalized guidance. Here's how it works:

```
User Interface (React + TypeScript)
↓
API Layer (FastAPI)
↓
RAG Pipeline
  - Embedding Generation (OpenAI)
  - Vector Search (Vector DB)
  - Context Building
↓
LLM Integration (OpenAI)
↓
Storage Layer
  - Vector DB (Embeddings & Knowledge)
  - MongoDB (User Data & Metadata)
  - Redis (Active Sessions)
```

## 2. Core Features & Technical Implementation

### A. User Authentication
```
1. Frontend: React Login Form
   ↓
2. API: POST /api/v1/auth/login
   ↓
3. Backend: FastAPI + JWT
   ↓
4. Database: User table in MongoDB
   ↓
5. Response: JWT token for future requests
```

**Technology Stack:**
- Frontend: React 18 [https://react.dev/]
- Auth: JWT with bcrypt [https://jwt.io/]
- Database: MongoDB 6 [https://www.mongodb.com/]
- Validation: Pydantic 2.0 [https://docs.pydantic.dev/]

**Data Types:**
```typescript
interface User {
  id: string;
  email: string;
  passwordHash: string;
  lastLogin: Date;
}

interface AuthResponse {
  token: string;
  user: UserProfile;
}
```

### B. RAG Knowledge Base
```python
class KnowledgeChunk(BaseModel):
    id: str
    content: str
    embedding: List[float]
    metadata: ChunkMetadata
    last_used: datetime
    usage_count: int

class ChunkMetadata(BaseModel):
    type: Literal[
        'career_path',
        'learning_resource',
        'user_insight',
        'conversation',
        'mentor_advice'
    ]
    topics: List[str]
    importance: int  # 1-10
    source: str
    timestamp: datetime
```

### C. RAG Pipeline
```python
async def process_user_input(
    user_id: str,
    query: str,
    context_type: str
) -> Dict[str, Any]:
    # 1. Generate embedding
    query_embedding = await create_embedding(query)
    
    # 2. Get relevant chunks
    relevant_chunks = await vector_db.query(
        vector=query_embedding,
        filter={
            "metadata.type": context_type,
            "metadata.importance": {"$gte": 5}
        },
        limit=3
    )
    
    # 3. Build context
    context = build_context(relevant_chunks)
    
    # 4. Generate response
    response = await generate_ai_response(query, context)
    
    # 5. Save new knowledge
    if response.importance >= 7:
        await save_to_knowledge_base(
            content=response.content,
            metadata={
                "type": context_type,
                "user_id": user_id,
                "importance": response.importance
            }
        )
    
    return response
```

### D. Storage Strategy
```python
# 1. Vector Storage (Knowledge & Embeddings)
vector_db = {
    "chunks": [
        {
            "vector": [0.1, ...],  # 1536 dims
            "text": "content...",
            "metadata": {...}
        }
    ]
}

# 2. Document Storage (MongoDB)
user_data = {
    "profile": {...},
    "learning_progress": {...},
    "knowledge_map": {
        "chunk_ids": ["id1", "id2"],
        "relationships": [...]
    }
}

# 3. Cache Layer (Redis)
active_sessions = {
    "user:123:context": {
        "recent_chunks": ["id1", "id2"],
        "current_focus": "python_learning"
    }
}
```

### E. Benefits of RAG Implementation

1. **Cost Efficiency**
   - Reduced token usage
   - Smart context selection
   - Cached common responses

2. **Better Responses**
   - Uses real examples
   - Remembers user context
   - Consistent advice

3. **Personalization**
   - Learning style adaptation
   - Progress-based responses
   - Career-specific guidance

4. **Knowledge Building**
   - Grows with each interaction
   - Learns from user successes
   - Maintains context history

### F. Implementation Notes

1. **Vector DB Setup**
   ```python
   from langchain.vectorstores import Milvus
   
   vector_store = Milvus(
       embedding_function=OpenAIEmbeddings(),
       connection_args={
           "host": "localhost",
           "port": 19530
       }
   )
   ```

2. **Embedding Pipeline**
   ```python
   async def create_embedding(text: str) -> List[float]:
       response = await openai.Embedding.create(
           input=text,
           model="text-embedding-ada-002"
       )
       return response.data[0].embedding
   ```

3. **Context Management**
   ```python
   def build_context(chunks: List[Dict]) -> str:
       return "\n".join([
           f"Context ({chunk['metadata']['type']}): {chunk['text']}"
           for chunk in chunks
       ])
   ```

### G. Chat System & Analysis
```
1. Real-time Processing Pipeline
   ↓
2. Importance Analysis (LLM)
   - Emotional signals
   - Decision points
   - Learning moments
   - Action commitments
   ↓
3. Context Integration
   - Previous insights
   - User goals
   - Career path
   ↓
4. Storage Decision
   - High importance → Long-term storage
   - Medium → Summarized
   - Low → Temporary cache
```

```python
async def process_message(message: str, user_id: str) -> Dict[str, Any]:
    # 1. Store in Redis for immediate access
    redis_key = f"chat:{user_id}:recent"
    await redis.lpush(redis_key, message)
    await redis.ltrim(redis_key, 0, 99)  # Keep last 100 messages

    # 2. Analyze importance with LLM
    analysis = await analyze_message_importance(message)
    
    # 3. Store based on importance
    if analysis.importance >= 7:
        # High importance - Store in MongoDB
        await store_important_message(message, analysis)
    elif analysis.importance >= 4:
        # Medium importance - Store summary
        await store_message_summary(message, analysis)
    
    # 4. Cleanup old messages (30+ days)
    if datetime.now().day == 1:  # Run monthly
        await cleanup_old_messages(user_id)
```

### H. Learning System
```
1. Frontend: Topic Selection
   ↓
2. API: GET /api/v1/learning/topics
   ↓
3. Backend: Progress Tracking
   ↓
4. AI: Personalized Path
   ↓
5. Database: Store Progress
```

**Technology Stack:**
- State Management: Zustand [https://zustand-demo.pmnd.rs/]
- API Client: React Query [https://tanstack.com/query/]
- Database: MongoDB with JSONB
- AI: GPT-4 for recommendations

**Data Structure:**
```typescript
interface Topic {
  id: string;
  name: string;
  content: {
    theory: string;
    exercises: Exercise[];
  };
  prerequisites: string[];
}

interface Progress {
  userId: string;
  topicId: string;
  status: 'started' | 'completed';
  score?: number;
}
```

## 3. Database Schema Evolution

### Phase 1: Basic Authentication
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE,
  password_hash VARCHAR
);
```

### Phase 2: Add User Profiles
```sql
CREATE TABLE user_profiles (
  user_id UUID REFERENCES users,
  name VARCHAR,
  interests JSONB,
  learning_style VARCHAR
);
```

### Phase 3: Chat System
```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users,
  title VARCHAR,
  created_at TIMESTAMP
);

CREATE TABLE messages (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES conversations,
  content TEXT,
  embedding vector(1536)
);
```

### Phase 4: Learning System
```sql
CREATE TABLE topics (
  id UUID PRIMARY KEY,
  name VARCHAR,
  content JSONB,
  prerequisites JSONB
);

CREATE TABLE progress (
  user_id UUID REFERENCES users,
  topic_id UUID REFERENCES topics,
  status VARCHAR,
  completed_at TIMESTAMP
);
```

## 4. API Endpoints Evolution

### Phase 1: Authentication
```
POST /api/v1/auth/login
POST /api/v1/auth/register
POST /api/v1/auth/refresh
```

### Phase 2: User Management
```
GET /api/v1/users/profile
PUT /api/v1/users/profile
GET /api/v1/users/settings
```

### Phase 3: Chat System
```
WebSocket /api/v1/chat
GET /api/v1/chat/history
POST /api/v1/chat/feedback
```

### Phase 4: Learning System
```
GET /api/v1/learning/topics
POST /api/v1/learning/progress
GET /api/v1/learning/recommendations
```

## 5. Development Setup

### Local Environment
```bash
# 1. Clone repository
git clone https://github.com/your/repo.git
cd repo

# 2. Frontend setup
cd frontend
pnpm install
pnpm dev  # Runs on :3000

# 3. Database setup
docker-compose up -d  # MongoDB + Vector DB + Redis

# 4. Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload  # Runs on :8000
```

### Environment Variables
```env
# Frontend (.env.local)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Backend (.env)
DATABASE_URL=mongodb://user:pass@localhost:27017/ponder
OPENAI_API_KEY=sk-...
JWT_SECRET=your-secret-key
```

## 6. Deployment Pipeline

### Development
```
Local Development
↓
GitHub Push
↓
GitHub Actions (CI)
↓
Preview Environment
```

### Staging
```
Merge to Staging
↓
Automatic Deploy
↓
E2E Tests
↓
Manual QA
```

### Production
```
Merge to Main
↓
Build Process
↓
Deploy Frontend (Vercel)
↓
Deploy Backend (Railway)
↓
Database (Supabase)
```

## 7. Monitoring & Analytics

### Performance Tracking
```
Application Metrics
↓
Prometheus
↓
Grafana Dashboards
↓
Alert System
```

### Error Tracking
```
Application Error
↓
Sentry Capture
↓
Error Classification
↓
Team Notification
```

Each section shows the complete flow from user interaction to data storage, making it clear how each piece connects and evolves. Would you like me to explain any specific flow in more detail?
