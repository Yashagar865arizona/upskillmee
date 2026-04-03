"""
Load testing script for Ponder API using Locust.
Tests critical endpoints under various load conditions.
"""

import json
import random
import time
import uuid
from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask
import websocket
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PonderUser(HttpUser):
    """Simulates a user interacting with the Ponder platform."""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Initialize user session."""
        self.token = None
        self.user_id = None
        self.conversation_id = None
        self.register_and_login()
    
    def register_and_login(self):
        """Register a new user and login to get auth token."""
        # Generate unique user credentials
        user_email = f"loadtest_{uuid.uuid4().hex[:8]}@example.com"
        user_password = "LoadTest123!"
        
        # Register user
        register_data = {
            "email": user_email,
            "password": user_password,
            "name": f"Load Test User {uuid.uuid4().hex[:6]}"
        }
        
        with self.client.post("/api/v1/auth/register", 
                             json=register_data, 
                             catch_response=True) as response:
            if response.status_code == 201:
                response.success()
                logger.info(f"User registered: {user_email}")
            else:
                response.failure(f"Registration failed: {response.text}")
                raise RescheduleTask()
        
        # Login to get token
        login_data = {
            "email": user_email,
            "password": user_password
        }
        
        with self.client.post("/api/v1/auth/login", 
                             json=login_data, 
                             catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                response.success()
                logger.info(f"User logged in: {user_email}")
            else:
                response.failure(f"Login failed: {response.text}")
                raise RescheduleTask()
    
    def get_auth_headers(self):
        """Get authorization headers."""
        if not self.token:
            self.register_and_login()
        return {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def send_chat_message(self):
        """Send a chat message via REST API."""
        messages = [
            "Hello, how are you?",
            "Can you help me learn Python?",
            "What's the best way to start web development?",
            "I want to build a mobile app",
            "Tell me about machine learning",
            "How do I improve my coding skills?",
            "What programming language should I learn first?",
            "Can you create a learning plan for me?"
        ]
        
        message_data = {
            "message": random.choice(messages),
            "agent_mode": random.choice(["chat", "work", "plan"])
        }
        
        with self.client.post("/api/v1/chat/message", 
                             json=message_data,
                             headers=self.get_auth_headers(),
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Chat message failed: {response.text}")
    
    @task(2)
    def get_user_profile(self):
        """Get user profile information."""
        with self.client.get("/api/v1/users/profile",
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get profile failed: {response.text}")
    
    @task(2)
    def get_learning_plans(self):
        """Get user's learning plans."""
        with self.client.get("/api/v1/learning/plans",
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get learning plans failed: {response.text}")
    
    @task(1)
    def generate_learning_plan(self):
        """Generate a new learning plan."""
        topics = [
            "Python programming",
            "Web development",
            "Data science",
            "Machine learning",
            "Mobile app development",
            "DevOps",
            "Cybersecurity"
        ]
        
        plan_data = {
            "topic": random.choice(topics),
            "difficulty": random.choice(["beginner", "intermediate", "advanced"]),
            "time_commitment": random.randint(5, 20)
        }
        
        with self.client.post("/api/v1/learning/generate-plan",
                             json=plan_data,
                             headers=self.get_auth_headers(),
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Generate plan failed: {response.text}")
    
    @task(1)
    def get_user_projects(self):
        """Get user's projects."""
        with self.client.get("/api/v1/users/projects",
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get projects failed: {response.text}")
    
    @task(1)
    def get_analytics(self):
        """Get user analytics."""
        with self.client.get("/api/v1/analytics/user-stats",
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get analytics failed: {response.text}")
    
    @task(1)
    def health_check(self):
        """Check system health."""
        with self.client.get("/api/v1/health",
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.text}")


class WebSocketUser(HttpUser):
    """Simulates WebSocket connections for real-time chat."""
    
    wait_time = between(2, 8)
    
    def on_start(self):
        """Initialize WebSocket connection."""
        self.token = None
        self.user_id = None
        self.ws = None
        self.register_and_login()
        self.connect_websocket()
    
    def register_and_login(self):
        """Register and login to get auth token."""
        user_email = f"wstest_{uuid.uuid4().hex[:8]}@example.com"
        user_password = "WSTest123!"
        
        # Register
        register_data = {
            "email": user_email,
            "password": user_password,
            "name": f"WS Test User {uuid.uuid4().hex[:6]}"
        }
        
        response = self.client.post("/api/v1/auth/register", json=register_data)
        if response.status_code != 201:
            raise RescheduleTask()
        
        # Login
        login_data = {
            "email": user_email,
            "password": user_password
        }
        
        response = self.client.post("/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id")
        else:
            raise RescheduleTask()
    
    def connect_websocket(self):
        """Connect to WebSocket endpoint."""
        try:
            # Convert HTTP URL to WebSocket URL
            ws_url = self.host.replace("http://", "ws://").replace("https://", "wss://")
            ws_url += "/api/v1/chat/ws"
            
            self.ws = websocket.create_connection(ws_url, timeout=10)
            
            # Send auth message
            auth_message = {
                "type": "auth",
                "token": self.token
            }
            self.ws.send(json.dumps(auth_message))
            
            # Wait for auth acknowledgment
            response = self.ws.recv()
            auth_response = json.loads(response)
            
            if auth_response.get("status") != "acknowledged":
                logger.error("WebSocket auth failed")
                self.ws.close()
                self.ws = None
                
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.ws = None
    
    @task(5)
    def send_websocket_message(self):
        """Send message via WebSocket."""
        if not self.ws:
            self.connect_websocket()
            if not self.ws:
                return
        
        messages = [
            "Hello via WebSocket!",
            "Can you help me with coding?",
            "What should I learn next?",
            "I need help with my project",
            "Explain machine learning to me"
        ]
        
        message_data = {
            "type": "message",
            "message": random.choice(messages),
            "agent_mode": random.choice(["chat", "work", "plan"]),
            "chat_history": []
        }
        
        try:
            start_time = time.time()
            self.ws.send(json.dumps(message_data))
            
            # Wait for response
            response = self.ws.recv()
            end_time = time.time()
            
            response_data = json.loads(response)
            
            if "text" in response_data:
                # Record successful WebSocket interaction
                events.request_success.fire(
                    request_type="WebSocket",
                    name="send_message",
                    response_time=(end_time - start_time) * 1000,
                    response_length=len(response)
                )
            else:
                events.request_failure.fire(
                    request_type="WebSocket",
                    name="send_message",
                    response_time=(end_time - start_time) * 1000,
                    response_length=len(response),
                    exception="Invalid response format"
                )
                
        except Exception as e:
            events.request_failure.fire(
                request_type="WebSocket",
                name="send_message",
                response_time=0,
                response_length=0,
                exception=str(e)
            )
            # Reconnect on error
            self.connect_websocket()
    
    def on_stop(self):
        """Clean up WebSocket connection."""
        if self.ws:
            self.ws.close()


# Custom load test scenarios
class HighLoadUser(PonderUser):
    """User that generates high load with minimal wait time."""
    wait_time = between(0.1, 0.5)


class BurstUser(PonderUser):
    """User that sends bursts of requests."""
    wait_time = between(0.1, 10)
    
    @task(10)
    def burst_chat_messages(self):
        """Send multiple chat messages in quick succession."""
        for _ in range(random.randint(3, 8)):
            self.send_chat_message()
            time.sleep(0.1)


# Performance monitoring events
@events.request_success.add_listener
def on_request_success(request_type, name, response_time, response_length, **kwargs):
    """Log successful requests for performance analysis."""
    if response_time > 2000:  # Log slow requests (>2s)
        logger.warning(f"Slow request: {request_type} {name} took {response_time}ms")

@events.request_failure.add_listener
def on_request_failure(request_type, name, response_time, response_length, exception, **kwargs):
    """Log failed requests for error analysis."""
    logger.error(f"Request failed: {request_type} {name} - {exception}")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize load test."""
    logger.info("Load test starting...")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Clean up after load test."""
    logger.info("Load test completed.")