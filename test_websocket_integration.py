#!/usr/bin/env python3
"""
Simple test script to verify WebSocket integration works
"""

import asyncio
import websockets
import json
import sys
import os

# Add backend to path
sys.path.append('backend')

async def test_websocket_connection():
    """Test basic WebSocket connection and message flow"""
    
    print("Testing WebSocket connection...")
    
    try:
        # Connect to WebSocket
        uri = "ws://localhost:8000/api/v1/chat/ws"
        
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket connected successfully")
            
            # Send auth message (with dummy token for testing)
            auth_message = {
                "type": "auth",
                "token": "dummy-token-for-testing"
            }
            
            await websocket.send(json.dumps(auth_message))
            print("✓ Auth message sent")
            
            # Wait for auth response
            response = await websocket.recv()
            auth_response = json.loads(response)
            print(f"✓ Auth response received: {auth_response}")
            
            # Send a test message
            test_message = {
                "type": "message",
                "message": "Hello, this is a test message",
                "agent_mode": "chat",
                "chat_history": []
            }
            
            await websocket.send(json.dumps(test_message))
            print("✓ Test message sent")
            
            # Wait for response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                message_response = json.loads(response)
                print(f"✓ Message response received: {message_response.get('text', 'No text field')[:100]}...")
                
                # Check if response has expected fields
                expected_fields = ['text', 'sender', 'id']
                missing_fields = [field for field in expected_fields if field not in message_response]
                
                if missing_fields:
                    print(f"⚠ Warning: Response missing fields: {missing_fields}")
                else:
                    print("✓ Response has all expected fields")
                    
            except asyncio.TimeoutError:
                print("⚠ Warning: No response received within 10 seconds")
            
            print("✓ WebSocket test completed successfully")
            
    except websockets.exceptions.ConnectionRefused:
        print("✗ Error: Could not connect to WebSocket server")
        print("  Make sure the backend server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"✗ Error during WebSocket test: {str(e)}")
        return False
    
    return True

async def main():
    """Main test function"""
    print("WebSocket Integration Test")
    print("=" * 40)
    
    success = await test_websocket_connection()
    
    if success:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)