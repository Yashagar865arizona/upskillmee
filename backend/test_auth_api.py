#!/usr/bin/env python3
"""
Test auth API endpoints
"""

import sys
import os
import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

def test_auth_endpoints():
    """Test auth API endpoints"""
    
    print("=== Testing Auth API Endpoints ===")
    print("Make sure the backend server is running on localhost:8000")
    print()
    
    # Test registration
    print("1. Testing Registration...")
    register_data = {
        "username": "testuser",
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
        print(f"Registration Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Registration successful")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Registration failed: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:8000")
        return
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
    
    print()
    
    # Test login
    print("2. Testing Login...")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        print(f"Login Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Login successful")
            result = response.json()
            print(f"Access Token: {result['access_token'][:50]}...")
            access_token = result['access_token']
        else:
            print(f"❌ Login failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return
    
    print()
    
    # Test /me endpoint
    print("3. Testing /me endpoint...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
        print(f"/me Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ /me endpoint successful")
            print(f"User data: {response.json()}")
        else:
            print(f"❌ /me failed: {response.text}")
    except Exception as e:
        print(f"❌ /me error: {str(e)}")
    
    print()
    
    # Test logout
    print("4. Testing Logout...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/logout", headers=headers)
        print(f"Logout Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Logout successful")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Logout failed: {response.text}")
    except Exception as e:
        print(f"❌ Logout error: {str(e)}")
    
    print()
    print("=== Auth API Test Complete ===")

if __name__ == "__main__":
    test_auth_endpoints()