"""
Router package for the AI mentoring application.

Each router follows a consistent class-based pattern with a 'router' attribute,
ensuring backward compatibility with the main.py application.

Routers:
- auth_router: Authentication operations (login, registration, password reset)
- chat_router: Chat and messaging features (messages, streaming, feedback)
- embedding_router: Embedding operations (statistics, creation, search)
- learning_router: Learning plan management and analytics
- user_router: User profile management and statistics
"""

# Import all routers to expose them to the main application
from .auth_router import router as auth_router
from .memory_router import router as memory_router
from .analytics_router import router as analytics_router
from .user_projects_router import router as user_projects_router

# Import routers that export classes
from .chat_router import router as chat_router_obj
from .embedding_router import router as embedding_router_obj
from .learning_router import router as learning_router_obj
from .user_router import router as user_router_obj

# Extract the actual router objects
chat_router = chat_router_obj.router if hasattr(chat_router_obj, 'router') else chat_router_obj
embedding_router = embedding_router_obj.router if hasattr(embedding_router_obj, 'router') else embedding_router_obj
learning_router = learning_router_obj.router if hasattr(learning_router_obj, 'router') else learning_router_obj
user_router = user_router_obj.router if hasattr(user_router_obj, 'router') else user_router_obj

__all__ = [
    "auth_router",
    "memory_router",
    "analytics_router",
    "user_projects_router",
    "chat_router", 
    "embedding_router",
    "learning_router",
    "user_router"
]
