"""
Services package for the application.
Consolidated and cleaned up services following single responsibility principle:
- AI functionality consolidated into ai_integration_service
- Learning plan generation integrated with AI service
- Duplicate functionality removed
- Unused imports cleaned up
"""

from .message_service import MessageService
from .learning_service import LearningService
from .embedding_service import EmbeddingService
from .auth_service import AuthService
from .user_service import UserService
from .project_service import ProjectService
from .health_service import HealthService
from .analytics_service import AnalyticsService
from .data_management_service import DataManagementService
from .ai_integration_service import AIIntegrationService
from .memory_service import MemoryService
from .admin_service import AdminService

__all__ = [
    'MessageService',
    'LearningService',  # Simplified to database operations only
    'EmbeddingService',
    'AuthService',
    'UserService',
    'ProjectService',
    'HealthService',
    'AnalyticsService',  # Consolidated duplicate methods
    'DataManagementService',
    'AIIntegrationService',  # Now includes learning plan generation
    'MemoryService',  # Cleaned up unused imports
    'AdminService'
]
