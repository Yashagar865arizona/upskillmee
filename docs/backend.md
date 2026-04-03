# Backend Architecture

## Core Services (`/app/services/`)

### AI and Chat
- `message_service.py` - Core AI chat service that handles conversations, context management, and OpenAI integration
- `embedding_service.py` - Manages vector embeddings for semantic search and context retrieval using FAISS
- `learning_service.py` - Generates personalized learning plans and adapts them based on user progress

### User Management
- `onboarding_service.py` - Handles 3-step user onboarding flow with career path exploration
- `user_service.py` - Manages user profiles, preferences, and authentication
- `project_service.py` - Handles project templates, progress tracking, and customization

### Performance and Monitoring
- `mentor_metrics_service.py` - Tracks user engagement, learning progress, and AI effectiveness
- `analytics_service.py` - Collects and analyzes user behavior and system performance
- `cache_service.py` - Implements caching strategies for improved performance
- `background_tasks.py` - Manages asynchronous task processing
- `health_service.py` - Monitors service health and dependencies

## Database Models (`/app/models/`)

### Core Models
- `base.py` - Base SQLAlchemy model configuration
- `base_model.py` - Common model functionality and mixins
- `schemas.py` - Pydantic schemas for request/response validation

### Domain Models
- `user.py` - User, UserProfile, UserProject, and UserSnapshot models
- `chat.py` - Conversation and Message models with embedding support
- `message_models.py` - Additional message-related models and schemas

## API Routes (`/app/routers/`)

### Main Routes
- `chat_router.py` - Chat endpoints for messaging and streaming responses
- `learning_router.py` - Learning plan and progress tracking endpoints
- `user_router.py` - User management and profile endpoints

### Supporting Routes
- `embedding_router.py` - Vector embedding and semantic search endpoints
- `onboarding_router.py` - User onboarding flow endpoints

## Database (`/app/database/`)

### Core Database
- `database.py` - Database connection pool and session management
- `base.py` - SQLAlchemy declarative base setup
- `engine.py` - Database engine configuration
- `session.py` - Session factory and context management
- `init_db.py` - Database initialization and setup

## Monitoring (`/app/monitoring/`)

### Metrics
- `metrics.py` - Prometheus metrics for AI, cache, and system performance

## Database Migrations (`/alembic/`)

### Version Control
- `env.py` - Alembic environment configuration
- `script.py.mako` - Migration script template

### Migrations
- `versions/001_create_tables.py` - Initial schema creation
- `versions/002_add_constraints_and_indexes.py` - Database constraints and indexing
- `versions/003_enhance_user_profiles.py` - Extended user profile fields
- `versions/004_merge_heads.py` - Migration branch merging
- `versions/xxx_add_message_embeddings.py` - Message embedding support

## Configuration (`/app/config/`)

### Settings
- `settings.py` - Core application settings and environment variable management
- `defaults.py` - Default configuration values and constants
- `__init__.py` - Configuration module initialization and exports

## Application Entry (`/app/`)

### Core Application
- `main.py` - FastAPI application setup, middleware configuration, and router registration
- `database.py` - Core database configuration and connection management

## Middleware (`/app/middleware/`)

### Request Processing
- `monitoring.py` - Request monitoring and performance tracking middleware
- `rate_limiter.py` - Rate limiting implementation for API endpoints

## Scripts (`/backend/scripts/`)

### Utilities
- `export_metrics.py` - Exports monitoring metrics for analysis

## Configuration

### Environment
- `.env` - Environment variables for API keys and settings
- `requirements.txt` - Python package dependencies

### Setup
- `setup.py` - Package installation configuration
- `pyproject.toml` - Poetry dependency management
- `alembic.ini` - Database migration configuration

## Testing
- `test_chat.py` - Chat functionality tests
- `test_onboarding.py` - Onboarding flow tests

## Scripts
- `reset_db.py` - Database reset and reinitialization
- `install-poetry.py` - Poetry installation helper
