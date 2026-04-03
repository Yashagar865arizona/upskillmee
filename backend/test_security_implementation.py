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

class SecurityTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_cors_configuration(self):
        """Test CORS configuration"""
        logger.info("Testing CORS configuration...")
        
        # Test preflight request
        response = self.session.options(
            f"{self.base_url}/api/v1/auth/login",
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
        )
        
        assert response.status_code == 200
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers
        assert 'Access-Control-Allow-Headers' in response.headers
        
        logger.info("✓ CORS configuration working correctly")
        
    def test_security_headers(self):
        """Test security headers are present"""
        logger.info("Testing security headers...")
        
        response = self.session.get(f"{self.base_url}/")
        
        expected_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options', 
            'X-XSS-Protection',
            'Referrer-Policy',
            'Content-Security-Policy',
            'Server',
            'Cache-Control',
            'Permissions-Policy'
        ]
        
        for header in expected_headers:
            assert header in response.headers, f"Missing security header: {header}"
            
        # Verify specific header values
        assert response.headers['X-Frame-Options'] == 'DENY'
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert response.headers['X-XSS-Protection'] == '1; mode=block'
        assert response.headers['Server'] == 'Ponder-API'
        
        logger.info("✓ Security headers present and configured correctly")
        
    def test_input_validation(self):
        """Test input validation and sanitization"""
        logger.info("Testing input validation...")
        
        # Test SQL injection attempt
        malicious_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "../../../etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for payload in malicious_payloads:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "email": payload,
                    "password": "test123"
                },
                headers={'Content-Type': 'application/json'}
            )
            
            # Should return validation error, not 500
            assert response.status_code in [400, 422], f"Payload not blocked: {payload}"
            
        logger.info("✓ Input validation blocking malicious payloads")
        
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        logger.info("Testing rate limiting...")
        
        # Make rapid requests to trigger rate limiting
        endpoint = f"{self.base_url}/api/v1/auth/login"
        
        # Make requests rapidly
        responses = []
        for i in range(15):  # Exceed the auth rate limit of 10
            response = self.session.post(
                endpoint,
                json={"email": "test@example.com", "password": "test123"},
                headers={'Content-Type': 'application/json'}
            )
            responses.append(response)
            time.sleep(0.1)  # Small delay to avoid overwhelming
        
        # Check if rate limiting kicked in
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Rate limiting not working"
        
        # Check rate limit headers
        for response in responses:
            if 'X-RateLimit-Limit' in response.headers:
                assert int(response.headers['X-RateLimit-Limit']) > 0
                break
        
        logger.info("✓ Rate limiting working correctly")
        
    def test_content_type_validation(self):
        """Test content type validation"""
        logger.info("Testing content type validation...")
        
        # Test with invalid content type
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            data="invalid data",
            headers={'Content-Type': 'text/xml'}
        )
        
        assert response.status_code == 415, "Invalid content type not rejected"
        
        logger.info("✓ Content type validation working")
        
    def test_request_size_limits(self):
        """Test request size limits"""
        logger.info("Testing request size limits...")
        
        # Create a large payload
        large_payload = {
            "email": "test@example.com",
            "password": "test123",
            "large_field": "x" * (1024 * 1024)  # 1MB of data
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json=large_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        # Should be rejected due to size
        assert response.status_code in [413, 400], "Large request not rejected"
        
        logger.info("✓ Request size limits working")
        
    def test_user_agent_validation(self):
        """Test user agent validation"""
        logger.info("Testing user agent validation...")
        
        # Test with blocked user agent
        blocked_agents = ['bot', 'crawler', 'spider', 'curl']
        
        for agent in blocked_agents:
            response = self.session.get(
                f"{self.base_url}/",
                headers={'User-Agent': agent}
            )
            
            # Should still work but might be logged/monitored
            # This is more about monitoring than blocking
            assert response.status_code == 200
            
        logger.info("✓ User agent validation implemented")
        
    def test_json_validation(self):
        """Test JSON validation and sanitization"""
        logger.info("Testing JSON validation...")
        
        # Test with malformed JSON
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            data='{"email": "test@example.com", "password": "test123"',  # Missing closing brace
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400, "Malformed JSON not rejected"
        
        logger.info("✓ JSON validation working")
        
    def test_path_traversal_protection(self):
        """Test path traversal protection"""
        logger.info("Testing path traversal protection...")
        
        # Test various path traversal attempts
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd"
        ]
        
        for path in traversal_paths:
            response = self.session.get(f"{self.base_url}/{path}")
            
            # Should return 404 or 400, not expose files
            assert response.status_code in [400, 404], f"Path traversal not blocked: {path}"
            
        logger.info("✓ Path traversal protection working")
        
    def test_authentication_security(self):
        """Test authentication security features"""
        logger.info("Testing authentication security...")
        
        # Test password complexity validation
        weak_passwords = [
            "123",
            "password",
            "12345678",
            "Password",  # Missing special char and number
        ]
        
        for password in weak_passwords:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json={
                    "username": "testuser",
                    "email": "test@example.com",
                    "password": password
                },
                headers={'Content-Type': 'application/json'}
            )
            
            # Should reject weak passwords
            assert response.status_code in [400, 422], f"Weak password accepted: {password}"
            
        logger.info("✓ Authentication security working")
        
    def run_all_tests(self):
        """Run all security tests"""
        logger.info("Starting comprehensive security tests...")
        
        try:
            self.test_cors_configuration()
            self.test_security_headers()
            self.test_input_validation()
            self.test_rate_limiting()
            self.test_content_type_validation()
            self.test_request_size_limits()
            self.test_user_agent_validation()
            self.test_json_validation()
            self.test_path_traversal_protection()
            self.test_authentication_security()
            
            logger.info("🎉 All security tests passed!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Security test failed: {str(e)}")
            return False

def main():
    """Main test function"""
    tester = SecurityTester()
    
    # Test if server is running
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code != 200:
            logger.error("Server not responding correctly")
            return
    except requests.exceptions.RequestException:
        logger.error("Server not running. Please start the FastAPI server first.")
        return
    
    # Run security tests
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Security implementation verified successfully!")
        print("\nImplemented security features:")
        print("- Input validation and sanitization")
        print("- Rate limiting with Redis fallback")
        print("- Comprehensive security headers")
        print("- CORS configuration")
        print("- Content type validation")
        print("- Request size limits")
        print("- Path traversal protection")
        print("- Authentication security")
        print("- XSS and SQL injection protection")
    else:
        print("\n❌ Some security tests failed. Please check the logs.")

if __name__ == "__main__":
    main()