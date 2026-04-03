"""
Test script to verify security hardening implementation.
"""

import asyncio
import json
import time
import requests
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityHardeningTest:
    """Test suite for security hardening features"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_security_headers(self) -> Dict[str, Any]:
        """Test that security headers are properly set"""
        logger.info("Testing security headers...")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            headers = response.headers
            
            expected_headers = {
                'X-Frame-Options': 'DENY',
                'X-Content-Type-Options': 'nosniff',
                'X-XSS-Protection': '1; mode=block',
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                'Content-Security-Policy': True,  # Just check if present
                'Permissions-Policy': True,
                'Server': 'Ponder-API'
            }
            
            results = {}
            for header, expected_value in expected_headers.items():
                if header in headers:
                    if expected_value is True:
                        results[header] = "✓ Present"
                    elif headers[header] == expected_value:
                        results[header] = "✓ Correct"
                    else:
                        results[header] = f"✗ Wrong value: {headers[header]}"
                else:
                    results[header] = "✗ Missing"
            
            return {
                "test": "Security Headers",
                "status": "PASS" if all("✓" in v for v in results.values()) else "FAIL",
                "details": results
            }
            
        except Exception as e:
            return {
                "test": "Security Headers",
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_cors_configuration(self) -> Dict[str, Any]:
        """Test CORS configuration"""
        logger.info("Testing CORS configuration...")
        
        try:
            # Test preflight request
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            response = self.session.options(f"{self.base_url}/api/v1/auth/login", headers=headers)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            return {
                "test": "CORS Configuration",
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "details": cors_headers
            }
            
        except Exception as e:
            return {
                "test": "CORS Configuration",
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_input_validation(self) -> Dict[str, Any]:
        """Test input validation and sanitization"""
        logger.info("Testing input validation...")
        
        test_cases = [
            {
                "name": "SQL Injection",
                "payload": {"email": "test@example.com'; DROP TABLE users; --", "password": "password123"},
                "expected_status": 400
            },
            {
                "name": "XSS Attack",
                "payload": {"email": "test@example.com", "password": "<script>alert('xss')</script>"},
                "expected_status": 400
            },
            {
                "name": "Path Traversal",
                "payload": {"email": "../../../etc/passwd", "password": "password123"},
                "expected_status": 400
            },
            {
                "name": "Oversized Input",
                "payload": {"email": "test@example.com", "password": "a" * 10000},
                "expected_status": 400
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json=test_case["payload"],
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == test_case["expected_status"]:
                    results[test_case["name"]] = "✓ Blocked"
                else:
                    results[test_case["name"]] = f"✗ Not blocked (status: {response.status_code})"
                    
            except Exception as e:
                results[test_case["name"]] = f"✗ Error: {str(e)}"
        
        return {
            "test": "Input Validation",
            "status": "PASS" if all("✓" in v for v in results.values()) else "FAIL",
            "details": results
        }
    
    def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting functionality"""
        logger.info("Testing rate limiting...")
        
        try:
            # Make rapid requests to trigger rate limiting
            endpoint = f"{self.base_url}/api/v1/auth/login"
            payload = {"email": "test@example.com", "password": "wrongpassword"}
            
            responses = []
            for i in range(15):  # Exceed the typical rate limit
                response = self.session.post(endpoint, json=payload)
                responses.append(response.status_code)
                time.sleep(0.1)  # Small delay between requests
            
            # Check if we got rate limited (429 status)
            rate_limited = any(status == 429 for status in responses)
            
            return {
                "test": "Rate Limiting",
                "status": "PASS" if rate_limited else "FAIL",
                "details": {
                    "total_requests": len(responses),
                    "rate_limited": rate_limited,
                    "status_codes": list(set(responses))
                }
            }
            
        except Exception as e:
            return {
                "test": "Rate Limiting",
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_content_type_validation(self) -> Dict[str, Any]:
        """Test content type validation"""
        logger.info("Testing content type validation...")
        
        try:
            # Test with invalid content type
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                data="invalid data",
                headers={'Content-Type': 'text/plain'}
            )
            
            # Should reject non-JSON content for JSON endpoints
            content_type_blocked = response.status_code in [400, 415, 422]
            
            return {
                "test": "Content Type Validation",
                "status": "PASS" if content_type_blocked else "FAIL",
                "details": {
                    "status_code": response.status_code,
                    "blocked": content_type_blocked
                }
            }
            
        except Exception as e:
            return {
                "test": "Content Type Validation",
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_request_size_limits(self) -> Dict[str, Any]:
        """Test request size limits"""
        logger.info("Testing request size limits...")
        
        try:
            # Create a large payload
            large_payload = {
                "email": "test@example.com",
                "password": "password123",
                "large_field": "x" * (1024 * 1024)  # 1MB of data
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=large_payload,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should reject oversized requests
            size_limited = response.status_code in [413, 400, 422]
            
            return {
                "test": "Request Size Limits",
                "status": "PASS" if size_limited else "FAIL",
                "details": {
                    "status_code": response.status_code,
                    "blocked": size_limited
                }
            }
            
        except Exception as e:
            return {
                "test": "Request Size Limits",
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_authentication_security(self) -> Dict[str, Any]:
        """Test authentication security features"""
        logger.info("Testing authentication security...")
        
        try:
            # Test with invalid token
            response = self.session.get(
                f"{self.base_url}/api/v1/auth/me",
                headers={'Authorization': 'Bearer invalid_token_here'}
            )
            
            # Should reject invalid tokens
            auth_secured = response.status_code == 401
            
            # Test without token
            response_no_token = self.session.get(f"{self.base_url}/api/v1/auth/me")
            no_token_secured = response_no_token.status_code in [401, 403]
            
            return {
                "test": "Authentication Security",
                "status": "PASS" if auth_secured and no_token_secured else "FAIL",
                "details": {
                    "invalid_token_blocked": auth_secured,
                    "no_token_blocked": no_token_secured
                }
            }
            
        except Exception as e:
            return {
                "test": "Authentication Security",
                "status": "ERROR",
                "error": str(e)
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all security tests"""
        logger.info("Starting comprehensive security hardening tests...")
        
        tests = [
            self.test_security_headers,
            self.test_cors_configuration,
            self.test_input_validation,
            self.test_rate_limiting,
            self.test_content_type_validation,
            self.test_request_size_limits,
            self.test_authentication_security
        ]
        
        results = []
        passed = 0
        failed = 0
        errors = 0
        
        for test_func in tests:
            try:
                result = test_func()
                results.append(result)
                
                if result["status"] == "PASS":
                    passed += 1
                elif result["status"] == "FAIL":
                    failed += 1
                else:
                    errors += 1
                    
            except Exception as e:
                logger.error(f"Test {test_func.__name__} failed with error: {e}")
                results.append({
                    "test": test_func.__name__,
                    "status": "ERROR",
                    "error": str(e)
                })
                errors += 1
        
        summary = {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "success_rate": f"{(passed / len(tests)) * 100:.1f}%"
        }
        
        return {
            "summary": summary,
            "results": results
        }

def main():
    """Main function to run security tests"""
    tester = SecurityHardeningTest()
    
    print("🔒 Security Hardening Test Suite")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding properly")
            return
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start the FastAPI server first.")
        print("   Run: uvicorn backend.app.main:app --reload")
        return
    
    print("✅ Server is running, starting tests...\n")
    
    # Run all tests
    test_results = tester.run_all_tests()
    
    # Print results
    print("\n📊 Test Results Summary")
    print("-" * 30)
    summary = test_results["summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Errors: {summary['errors']} ⚠️")
    print(f"Success Rate: {summary['success_rate']}")
    
    print("\n📋 Detailed Results")
    print("-" * 30)
    
    for result in test_results["results"]:
        status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
        print(f"{status_icon} {result['test']}: {result['status']}")
        
        if "details" in result:
            for key, value in result["details"].items():
                print(f"   {key}: {value}")
        
        if "error" in result:
            print(f"   Error: {result['error']}")
        
        print()
    
    # Overall assessment
    if summary["passed"] == summary["total_tests"]:
        print("🎉 All security tests passed! Your application is well-hardened.")
    elif summary["passed"] >= summary["total_tests"] * 0.8:
        print("⚠️  Most security tests passed, but some issues need attention.")
    else:
        print("🚨 Multiple security issues detected. Please review and fix.")

if __name__ == "__main__":
    main()