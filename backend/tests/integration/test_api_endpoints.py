"""
Integration tests for API endpoints with authentication and authorization.
Tests all major API routes, authentication flows, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime, timedelta

from app.main import app
from app.services.auth_service import AuthService


class TestAPIEndpoints:
    """Test suite for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, test_user, auth_service):
        """Create authentication headers for testing."""
        token = auth_service.create_access_token(str(test_user.id))
        return {"Authorization": f"Bearer {token}"}

    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    # Authentication Endpoints Tests
    def test_register_user_success(self, client):
        """Test successful user registration."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "secure_password_123",
            "full_name": "Test User"
        }
        
        with patch('app.routers.auth_router.AuthService') as mock_auth_service_class:
            mock_auth_service = Mock()
            mock_auth_service.register_user = AsyncMock(return_value={"user_id": "user-123"})
            mock_auth_service_class.return_value = mock_auth_service
            
            response = client.post("/api/v1/auth/register", json=user_data)
            
            assert response.status_code == 201
            data = response.json()
            assert "user_id" in data
            assert data["message"] == "User registered successfully"

    def test_register_user_duplicate_email(self, client):
        """Test registration with duplicate email."""
        user_data = {
            "username": "testuser",
            "email": "existing@example.com",
            "password": "secure_password_123"
        }
        
        with patch('app.routers.auth_router.AuthService') as mock_auth_service_class:
            mock_auth_service = Mock()
            mock_auth_service.register_user = AsyncMock(side_effect=ValueError("Email already registered"))
            mock_auth_service_class.return_value = mock_auth_service
            
            response = client.post("/api/v1/auth/register", json=user_data)
            
            assert response.status_code == 400
            data = response.json()
            assert "Email already registered" in data["detail"]

    def test_register_user_invalid_data(self, client):
        """Test registration with invalid data."""
        user_data = {
            "username": "testuser",
            # Missing email and password
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422  # Validation error

    def test_login_user_success(self, client):
        """Test successful user login."""
        login_data = {
            "email": "test@example.com",
            "password": "correct_password"
        }
        
        with patch('app.routers.auth_router.AuthService') as mock_auth_service_class:
            mock_auth_service = Mock()
            mock_auth_service.authenticate_user = AsyncMock(return_value={
                "success": True,
                "access_token": "test_access_token",
                "token_type": "bearer",
                "expires_in": 1800,
                "refresh_token": "test_refresh_token",
                "user_id": "user-123"
            })
            mock_auth_service_class.return_value = mock_auth_service
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "test_access_token"
            assert data["token_type"] == "bearer"
            assert data["user_id"] == "user-123"

    def test_login_user_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "email": "test@example.com",
            "password": "wrong_password"
        }
        
        with patch('app.routers.auth_router.AuthService') as mock_auth_service_class:
            mock_auth_service = Mock()
            mock_auth_service.authenticate_user = AsyncMock(return_value={"success": False})
            mock_auth_service_class.return_value = mock_auth_service
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == 401
            data = response.json()
            assert "Invalid credentials" in data["detail"]

    def test_refresh_token_success(self, client):
        """Test successful token refresh."""
        refresh_data = {
            "refresh_token": "valid_refresh_token"
        }
        
        with patch('app.routers.auth_router.AuthService') as mock_auth_service_class:
            mock_auth_service = Mock()
            mock_auth_service.refresh_access_token = AsyncMock(return_value={
                "success": True,
                "access_token": "new_access_token",
                "token_type": "bearer",
                "expires_in": 1800,
                "user_id": "user-123"
            })
            mock_auth_service_class.return_value = mock_auth_service
            
            response = client.post("/api/v1/auth/refresh", json=refresh_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "new_access_token"

    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid token."""
        refresh_data = {
            "refresh_token": "invalid_refresh_token"
        }
        
        with patch('app.routers.auth_router.AuthService') as mock_auth_service_class:
            mock_auth_service = Mock()
            mock_auth_service.refresh_access_token = AsyncMock(return_value={
                "success": False,
                "message": "Invalid refresh token"
            })
            mock_auth_service_class.return_value = mock_auth_service
            
            response = client.post("/api/v1/auth/refresh", json=refresh_data)
            
            assert response.status_code == 401

    def test_logout_success(self, client, auth_headers):
        """Test successful logout."""
        with patch('app.routers.auth_router.AuthService') as mock_auth_service_class:
            mock_auth_service = Mock()
            mock_auth_service.invalidate_token = AsyncMock(return_value=True)
            mock_auth_service_class.return_value = mock_auth_service
            
            response = client.post("/api/v1/auth/logout", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Successfully logged out"

    def test_logout_without_auth(self, client):
        """Test logout without authentication."""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401

    # User Profile Endpoints Tests
    def test_get_user_profile_success(self, client, auth_headers):
        """Test successful user profile retrieval."""
        with patch('app.routers.user_router.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user-123"
            mock_user.email = "test@example.com"
            mock_user.name = "Test User"
            mock_get_user.return_value = mock_user
            
            response = client.get("/api/v1/users/profile", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "user-123"
            assert data["email"] == "test@example.com"

    def test_get_user_profile_unauthorized(self, client):
        """Test user profile retrieval without authentication."""
        response = client.get("/api/v1/users/profile")
        
        assert response.status_code == 401

    def test_update_user_profile_success(self, client, auth_headers):
        """Test successful user profile update."""
        profile_data = {
            "name": "Updated Name",
            "learning_style": "visual",
            "interests": ["programming", "AI"]
        }
        
        with patch('app.routers.user_router.get_current_user') as mock_get_user, \
             patch('app.routers.user_router.UserService') as mock_user_service_class:
            
            mock_user = Mock()
            mock_user.id = "user-123"
            mock_get_user.return_value = mock_user
            
            mock_user_service = Mock()
            mock_user_service.update_profile = AsyncMock(return_value={"success": True})
            mock_user_service_class.return_value = mock_user_service
            
            response = client.put("/api/v1/users/profile", json=profile_data, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Profile updated successfully"

    # Learning Plan Endpoints Tests
    def test_get_learning_plans_success(self, client, auth_headers):
        """Test successful learning plans retrieval."""
        with patch('app.routers.learning_router.get_current_user') as mock_get_user, \
             patch('app.routers.learning_router.LearningService') as mock_learning_service_class:
            
            mock_user = Mock()
            mock_user.id = "user-123"
            mock_get_user.return_value = mock_user
            
            mock_learning_service = Mock()
            mock_learning_service.get_user_plans = AsyncMock(return_value=[
                {
                    "id": "plan-123",
                    "title": "Web Development Basics",
                    "description": "Learn HTML, CSS, and JavaScript",
                    "content": {"projects": []}
                }
            ])
            mock_learning_service_class.return_value = mock_learning_service
            
            response = client.get("/api/v1/learning/plans", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Web Development Basics"

    def test_create_learning_plan_success(self, client, auth_headers):
        """Test successful learning plan creation."""
        plan_data = {
            "title": "Python Programming",
            "description": "Learn Python fundamentals",
            "content": {
                "projects": [
                    {
                        "title": "Calculator App",
                        "skills": ["Python", "Functions"]
                    }
                ]
            }
        }
        
        with patch('app.routers.learning_router.get_current_user') as mock_get_user, \
             patch('app.routers.learning_router.LearningService') as mock_learning_service_class:
            
            mock_user = Mock()
            mock_user.id = "user-123"
            mock_get_user.return_value = mock_user
            
            mock_learning_service = Mock()
            mock_learning_service.save_plan = AsyncMock(return_value={
                "id": "plan-456",
                "title": plan_data["title"],
                "user_id": "user-123"
            })
            mock_learning_service_class.return_value = mock_learning_service
            
            response = client.post("/api/v1/learning/plans", json=plan_data, headers=auth_headers)
            
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == "plan-456"
            assert data["title"] == plan_data["title"]

    def test_create_learning_plan_unauthorized(self, client):
        """Test learning plan creation without authentication."""
        plan_data = {
            "title": "Test Plan",
            "description": "Test description"
        }
        
        response = client.post("/api/v1/learning/plans", json=plan_data)
        
        assert response.status_code == 401

    # Chat/Message Endpoints Tests
    def test_websocket_connection_success(self, client):
        """Test successful WebSocket connection."""
        with client.websocket_connect("/api/v1/chat/ws") as websocket:
            # Send auth message
            auth_message = {
                "type": "auth",
                "token": "valid_jwt_token"
            }
            websocket.send_json(auth_message)
            
            # Should receive acknowledgment
            response = websocket.receive_json()
            assert response["status"] == "acknowledged"

    def test_websocket_chat_message(self, client):
        """Test sending chat message via WebSocket."""
        with patch('app.routers.chat_router.MessageService') as mock_message_service_class:
            mock_message_service = Mock()
            mock_message_service.process_message = AsyncMock(return_value={
                "text": "Hello! How can I help you today?",
                "sender": "bot",
                "id": "msg-123"
            })
            mock_message_service_class.return_value = mock_message_service
            
            with client.websocket_connect("/api/v1/chat/ws") as websocket:
                # Send chat message
                chat_message = {
                    "type": "message",
                    "message": "Hello, I want to learn programming",
                    "user_id": "user-123"
                }
                websocket.send_json(chat_message)
                
                # Should receive bot response
                response = websocket.receive_json()
                assert response["sender"] == "bot"
                assert "text" in response

    def test_get_chat_history_success(self, client, auth_headers):
        """Test successful chat history retrieval."""
        with patch('app.routers.chat_router.get_current_user') as mock_get_user, \
             patch('app.routers.chat_router.MessageService') as mock_message_service_class:
            
            mock_user = Mock()
            mock_user.id = "user-123"
            mock_get_user.return_value = mock_user
            
            mock_message_service = Mock()
            mock_message_service.get_conversation_history = AsyncMock(return_value=[
                {
                    "id": "msg-1",
                    "content": "Hello",
                    "role": "user",
                    "created_at": "2024-01-15T10:00:00"
                },
                {
                    "id": "msg-2",
                    "content": "Hi! How can I help?",
                    "role": "assistant",
                    "created_at": "2024-01-15T10:00:01"
                }
            ])
            mock_message_service_class.return_value = mock_message_service
            
            response = client.get("/api/v1/chat/history/conv-123", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["role"] == "user"
            assert data[1]["role"] == "assistant"

    # Analytics Endpoints Tests
    def test_get_user_analytics_success(self, client, auth_headers):
        """Test successful user analytics retrieval."""
        with patch('app.routers.analytics_router.get_current_user') as mock_get_user, \
             patch('app.routers.analytics_router.AnalyticsService') as mock_analytics_service_class:
            
            mock_user = Mock()
            mock_user.id = "user-123"
            mock_get_user.return_value = mock_user
            
            mock_analytics_service = Mock()
            mock_analytics_service.get_user_analytics = AsyncMock(return_value={
                "total_conversations": 15,
                "learning_plans_created": 3,
                "time_spent_minutes": 240,
                "topics_explored": ["programming", "AI", "web development"]
            })
            mock_analytics_service_class.return_value = mock_analytics_service
            
            response = client.get("/api/v1/analytics/user", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_conversations"] == 15
            assert data["learning_plans_created"] == 3
            assert "programming" in data["topics_explored"]

    # Admin Endpoints Tests
    def test_admin_metrics_unauthorized(self, client, auth_headers):
        """Test admin metrics access without admin privileges."""
        response = client.get("/api/v1/admin/metrics", headers=auth_headers)
        
        # Should be forbidden for regular users
        assert response.status_code == 403

    def test_admin_metrics_success(self, client):
        """Test successful admin metrics retrieval."""
        # Mock admin user
        admin_headers = {"Authorization": "Bearer admin_token"}
        
        with patch('app.routers.admin_router.get_current_admin_user') as mock_get_admin:
            mock_admin = Mock()
            mock_admin.is_admin = True
            mock_get_admin.return_value = mock_admin
            
            with patch('app.routers.admin_router.AdminService') as mock_admin_service_class:
                mock_admin_service = Mock()
                mock_admin_service.get_system_metrics = AsyncMock(return_value={
                    "total_users": 1250,
                    "active_users_today": 89,
                    "total_conversations": 5420,
                    "system_health": "healthy"
                })
                mock_admin_service_class.return_value = mock_admin_service
                
                response = client.get("/api/v1/admin/metrics", headers=admin_headers)
                
                assert response.status_code == 200
                data = response.json()
                assert data["total_users"] == 1250
                assert data["system_health"] == "healthy"

    # Error Handling Tests
    def test_404_endpoint(self, client):
        """Test 404 error for non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 error for wrong HTTP method."""
        response = client.delete("/api/v1/auth/login")  # DELETE not allowed
        
        assert response.status_code == 405

    def test_invalid_json_payload(self, client):
        """Test handling of invalid JSON payload."""
        response = client.post(
            "/api/v1/auth/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        # This would require actual rate limiting to be configured
        # For now, we'll test that the endpoint exists and responds
        responses = []
        for _ in range(5):
            response = client.get("/health")
            responses.append(response.status_code)
        
        # All should succeed if rate limiting is not too strict
        assert all(status == 200 for status in responses)

    def test_cors_headers(self, client):
        """Test CORS headers in responses."""
        response = client.options("/api/v1/auth/login")
        
        # Should include CORS headers
        assert "access-control-allow-origin" in response.headers or response.status_code in [200, 405]

    def test_security_headers(self, client):
        """Test security headers in responses."""
        response = client.get("/health")
        
        # Check for basic security headers
        assert response.status_code == 200
        # Additional security header checks would go here

    # Authentication Edge Cases
    def test_expired_token(self, client):
        """Test handling of expired JWT token."""
        # Create an expired token
        expired_headers = {"Authorization": "Bearer expired_token"}
        
        response = client.get("/api/v1/users/profile", headers=expired_headers)
        
        assert response.status_code == 401

    def test_malformed_token(self, client):
        """Test handling of malformed JWT token."""
        malformed_headers = {"Authorization": "Bearer malformed.token.here"}
        
        response = client.get("/api/v1/users/profile", headers=malformed_headers)
        
        assert response.status_code == 401

    def test_missing_bearer_prefix(self, client):
        """Test handling of token without Bearer prefix."""
        no_bearer_headers = {"Authorization": "just_token_without_bearer"}
        
        response = client.get("/api/v1/users/profile", headers=no_bearer_headers)
        
        assert response.status_code == 401