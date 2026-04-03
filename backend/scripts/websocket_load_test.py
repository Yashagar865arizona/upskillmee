#!/usr/bin/env python3
"""
WebSocket load testing script for Ponder chat system.
Tests concurrent WebSocket connections and message throughput.
"""

import asyncio
import websockets
import json
import time
import logging
import statistics
from typing import List, Dict, Any
import aiohttp
import uuid
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

class WebSocketLoadTester:
    """Load tester for WebSocket connections."""
    
    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.http_base = base_url.replace("ws://", "http://").replace("wss://", "https://")
        self.results = {
            "connections": [],
            "messages": [],
            "errors": [],
            "summary": {}
        }
    
    async def register_and_login(self, session: aiohttp.ClientSession) -> str:
        """Register a test user and get auth token."""
        user_email = f"wsloadtest_{uuid.uuid4().hex[:8]}@example.com"
        user_password = "WSLoadTest123!"
        
        # Register user
        register_data = {
            "email": user_email,
            "password": user_password,
            "name": f"WS Load Test User {uuid.uuid4().hex[:6]}"
        }
        
        async with session.post(f"{self.http_base}/api/v1/auth/register", 
                               json=register_data) as response:
            if response.status != 201:
                raise Exception(f"Registration failed: {await response.text()}")
        
        # Login to get token
        login_data = {
            "email": user_email,
            "password": user_password
        }
        
        async with session.post(f"{self.http_base}/api/v1/auth/login", 
                               json=login_data) as response:
            if response.status != 200:
                raise Exception(f"Login failed: {await response.text()}")
            
            data = await response.json()
            return data.get("access_token")
    
    async def websocket_client(self, client_id: int, num_messages: int = 10, 
                              message_interval: float = 1.0) -> Dict[str, Any]:
        """Single WebSocket client that sends messages."""
        client_results = {
            "client_id": client_id,
            "connection_time": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "response_times": [],
            "errors": [],
            "status": "failed"
        }
        
        try:
            # Get auth token
            async with aiohttp.ClientSession() as session:
                token = await self.register_and_login(session)
            
            # Connect to WebSocket
            ws_url = f"{self.base_url}/api/v1/chat/ws"
            
            connection_start = time.time()
            async with websockets.connect(ws_url) as websocket:
                connection_time = time.time() - connection_start
                client_results["connection_time"] = connection_time
                
                logger.info(f"Client {client_id} connected in {connection_time:.3f}s")
                
                # Send auth message
                auth_message = {
                    "type": "auth",
                    "token": token
                }
                await websocket.send(json.dumps(auth_message))
                
                # Wait for auth acknowledgment
                auth_response = await websocket.recv()
                auth_data = json.loads(auth_response)
                
                if auth_data.get("status") != "acknowledged":
                    raise Exception("Authentication failed")
                
                # Send test messages
                messages = [
                    "Hello from WebSocket load test!",
                    "Can you help me learn Python?",
                    "What's the best way to start coding?",
                    "I want to build a web application",
                    "Tell me about machine learning",
                    "How do I improve my programming skills?",
                    "What should I learn next?",
                    "Can you create a learning plan for me?",
                    "I'm interested in data science",
                    "Help me with my coding project"
                ]
                
                for i in range(num_messages):
                    message_data = {
                        "type": "message",
                        "message": messages[i % len(messages)],
                        "agent_mode": "chat",
                        "chat_history": []
                    }
                    
                    # Send message and measure response time
                    send_time = time.time()
                    await websocket.send(json.dumps(message_data))
                    client_results["messages_sent"] += 1
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        receive_time = time.time()
                        response_time = receive_time - send_time
                        
                        response_data = json.loads(response)
                        
                        if "text" in response_data:
                            client_results["messages_received"] += 1
                            client_results["response_times"].append(response_time)
                            
                            logger.debug(f"Client {client_id} message {i+1}: {response_time:.3f}s")
                        else:
                            client_results["errors"].append(f"Invalid response format: {response}")
                    
                    except asyncio.TimeoutError:
                        client_results["errors"].append(f"Message {i+1} timeout")
                        logger.warning(f"Client {client_id} message {i+1} timeout")
                    
                    # Wait before sending next message
                    if i < num_messages - 1:
                        await asyncio.sleep(message_interval)
                
                client_results["status"] = "success"
                logger.info(f"Client {client_id} completed successfully")
        
        except Exception as e:
            client_results["errors"].append(str(e))
            logger.error(f"Client {client_id} error: {e}")
        
        return client_results
    
    async def run_load_test(self, num_clients: int = 10, messages_per_client: int = 5,
                           message_interval: float = 2.0, connection_delay: float = 0.1) -> Dict[str, Any]:
        """Run load test with multiple concurrent clients."""
        logger.info(f"Starting WebSocket load test:")
        logger.info(f"  - Clients: {num_clients}")
        logger.info(f"  - Messages per client: {messages_per_client}")
        logger.info(f"  - Message interval: {message_interval}s")
        logger.info(f"  - Connection delay: {connection_delay}s")
        
        start_time = time.time()
        
        # Create client tasks with staggered connections
        tasks = []
        for i in range(num_clients):
            # Stagger connection attempts to avoid overwhelming the server
            await asyncio.sleep(connection_delay)
            
            task = asyncio.create_task(
                self.websocket_client(i, messages_per_client, message_interval)
            )
            tasks.append(task)
        
        # Wait for all clients to complete
        client_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Process results
        successful_clients = []
        failed_clients = []
        all_response_times = []
        total_messages_sent = 0
        total_messages_received = 0
        total_errors = 0
        
        for result in client_results:
            if isinstance(result, Exception):
                failed_clients.append({"error": str(result)})
                total_errors += 1
            else:
                if result["status"] == "success":
                    successful_clients.append(result)
                    all_response_times.extend(result["response_times"])
                else:
                    failed_clients.append(result)
                
                total_messages_sent += result["messages_sent"]
                total_messages_received += result["messages_received"]
                total_errors += len(result["errors"])
        
        # Calculate statistics
        success_rate = len(successful_clients) / num_clients * 100
        message_success_rate = (total_messages_received / total_messages_sent * 100) if total_messages_sent > 0 else 0
        
        response_time_stats = {}
        if all_response_times:
            response_time_stats = {
                "min": min(all_response_times),
                "max": max(all_response_times),
                "mean": statistics.mean(all_response_times),
                "median": statistics.median(all_response_times),
                "p95": statistics.quantiles(all_response_times, n=20)[18] if len(all_response_times) >= 20 else max(all_response_times),
                "p99": statistics.quantiles(all_response_times, n=100)[98] if len(all_response_times) >= 100 else max(all_response_times)
            }
        
        throughput = total_messages_received / total_duration if total_duration > 0 else 0
        
        summary = {
            "test_duration": total_duration,
            "total_clients": num_clients,
            "successful_clients": len(successful_clients),
            "failed_clients": len(failed_clients),
            "success_rate": success_rate,
            "total_messages_sent": total_messages_sent,
            "total_messages_received": total_messages_received,
            "message_success_rate": message_success_rate,
            "total_errors": total_errors,
            "throughput_messages_per_second": throughput,
            "response_time_stats": response_time_stats
        }
        
        self.results = {
            "summary": summary,
            "successful_clients": successful_clients,
            "failed_clients": failed_clients,
            "timestamp": time.time()
        }
        
        return self.results
    
    def print_results(self):
        """Print load test results."""
        summary = self.results["summary"]
        
        print("\n" + "="*60)
        print("WEBSOCKET LOAD TEST RESULTS")
        print("="*60)
        
        print(f"Test Duration: {summary['test_duration']:.2f} seconds")
        print(f"Total Clients: {summary['total_clients']}")
        print(f"Successful Clients: {summary['successful_clients']}")
        print(f"Failed Clients: {summary['failed_clients']}")
        print(f"Client Success Rate: {summary['success_rate']:.1f}%")
        
        print(f"\nMessage Statistics:")
        print(f"  Messages Sent: {summary['total_messages_sent']}")
        print(f"  Messages Received: {summary['total_messages_received']}")
        print(f"  Message Success Rate: {summary['message_success_rate']:.1f}%")
        print(f"  Throughput: {summary['throughput_messages_per_second']:.2f} messages/second")
        print(f"  Total Errors: {summary['total_errors']}")
        
        response_stats = summary.get("response_time_stats", {})
        if response_stats:
            print(f"\nResponse Time Statistics:")
            print(f"  Min: {response_stats['min']:.3f}s")
            print(f"  Max: {response_stats['max']:.3f}s")
            print(f"  Mean: {response_stats['mean']:.3f}s")
            print(f"  Median: {response_stats['median']:.3f}s")
            print(f"  95th Percentile: {response_stats['p95']:.3f}s")
            print(f"  99th Percentile: {response_stats['p99']:.3f}s")
        
        # Print error summary
        failed_clients = self.results.get("failed_clients", [])
        if failed_clients:
            print(f"\nError Summary:")
            error_counts = {}
            for client in failed_clients:
                for error in client.get("errors", []):
                    error_counts[error] = error_counts.get(error, 0) + 1
            
            for error, count in error_counts.items():
                print(f"  {error}: {count} occurrences")
    
    def save_results(self, filename: str = None):
        """Save results to JSON file."""
        if not filename:
            timestamp = int(time.time())
            filename = f"websocket_load_test_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), "..", "reports", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {filepath}")
        return filepath


async def main():
    """Main function to run WebSocket load test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="WebSocket Load Test for Ponder")
    parser.add_argument("--url", default="ws://localhost:8000", help="WebSocket base URL")
    parser.add_argument("--clients", type=int, default=10, help="Number of concurrent clients")
    parser.add_argument("--messages", type=int, default=5, help="Messages per client")
    parser.add_argument("--interval", type=float, default=2.0, help="Interval between messages")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between client connections")
    parser.add_argument("--save", help="Save results to file")
    
    args = parser.parse_args()
    
    tester = WebSocketLoadTester(args.url)
    
    try:
        results = await tester.run_load_test(
            num_clients=args.clients,
            messages_per_client=args.messages,
            message_interval=args.interval,
            connection_delay=args.delay
        )
        
        tester.print_results()
        
        if args.save:
            tester.save_results(args.save)
        else:
            tester.save_results()
        
    except KeyboardInterrupt:
        logger.info("Load test interrupted by user")
    except Exception as e:
        logger.error(f"Load test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())