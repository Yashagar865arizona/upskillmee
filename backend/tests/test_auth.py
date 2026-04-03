#!/usr/bin/env python
"""
Simple test script to verify auth endpoints are working.
"""

import requests
import sys
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_auth_endpoints():
    """Test auth router endpoints are accessible."""
    
    endpoints = {
        "Login": {
            "url": "/api/v1/auth/login",
            "payload": {"email": "test@example.com", "password": "testpassword"}
        },
        "Register": {
            "url": "/api/v1/auth/register",
            "payload": {"email": "test@example.com", "password": "testpassword", "username": "testuser"}
        },
        "Register or Login": {
            "url": "/api/v1/auth/register-or-login",
            "payload": {"email": "test@example.com", "password": "testpassword", "is_new_user": False}
        }
    }
    
    success = True
    
    for name, config in endpoints.items():
        url = f"{API_BASE_URL}{config['url']}"
        payload = config["payload"]
        
        try:
            print(f"Testing {name} endpoint: {url}")
            
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # For this test, any response other than 404 is considered a success
            # because we're just testing that the endpoint exists and is correctly routed
            if response.status_code != 404:
                print(f"✅ {name} endpoint accessible (Status: {response.status_code})")
            else:
                print(f"❌ {name} endpoint not found (Status: 404)")
                success = False
            
            # Show response content
            try:
                resp_json = response.json()
                print(f"Response: {json.dumps(resp_json, indent=2)[:100]}...")
            except:
                print(f"Response: {response.text[:100]}...")
            
            print()
            
        except requests.exceptions.ConnectionError:
            print(f"❌ {name} endpoint connection error - is the server running?")
            success = False
        except Exception as e:
            print(f"❌ {name} endpoint error: {str(e)}")
            success = False
    
    return success

if __name__ == "__main__":
    print("Testing auth endpoints...")
    print("Note: These tests expect the server to be running at http://localhost:8000\n")
    
    if test_auth_endpoints():
        print("\n✅ All endpoints are accessible!")
        sys.exit(0)
    else:
        print("\n❌ Some endpoints are not accessible!")
        sys.exit(1) 