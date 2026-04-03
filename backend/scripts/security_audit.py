#!/usr/bin/env python3
"""
Comprehensive security audit script for Ponder backend.
Checks API endpoints, authentication, authorization, input validation, and GDPR compliance.
"""

import sys
import os
import json
import logging
import time
import re
from typing import Dict, List, Any, Optional
import requests
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityAuditor:
    """Comprehensive security auditor for the Ponder application."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.audit_results = {
            "timestamp": time.time(),
            "api_security": {},
            "authentication": {},
            "authorization": {},
            "input_validation": {},
            "gdpr_compliance": {},
            "code_security": {},
            "configuration_security": {},
            "recommendations": []
        }
    
    def audit_api_endpoints(self) -> Dict[str, Any]:
        """Audit API endpoints for security vulnerabilities."""
        logger.info("Auditing API endpoints...")
        
        endpoints_to_test = [
            # Public endpoints
            {"path": "/", "method": "GET", "expected_auth": False},
            {"path": "/test", "method": "GET", "expected_auth": False},
            {"path": "/api/v1/health", "method": "GET", "expected_auth": False},
            
            # Authentication endpoints
            {"path": "/api/v1/auth/register", "method": "POST", "expected_auth": False},
            {"path": "/api/v1/auth/login", "method": "POST", "expected_auth": False},
            {"path": "/api/v1/auth/logout", "method": "POST", "expected_auth": True},
            {"path": "/api/v1/auth/refresh", "method": "POST", "expected_auth": True},
            
            # Protected endpoints
            {"path": "/api/v1/users/profile", "method": "GET", "expected_auth": True},
            {"path": "/api/v1/chat/message", "method": "POST", "expected_auth": True},
            {"path": "/api/v1/learning/plans", "method": "GET", "expected_auth": True},
            {"path": "/api/v1/admin/users", "method": "GET", "expected_auth": True},
        ]
        
        results = {
            "endpoint_tests": [],
            "security_headers": {},
            "cors_configuration": {},
            "rate_limiting": {},
            "ssl_configuration": {}
        }
        
        for endpoint in endpoints_to_test:
            result = self.test_endpoint_security(endpoint)
            results["endpoint_tests"].append(result)
        
        # Test security headers
        results["security_headers"] = self.check_security_headers()
        
        # Test CORS configuration
        results["cors_configuration"] = self.check_cors_configuration()
        
        # Test rate limiting
        results["rate_limiting"] = self.check_rate_limiting()
        
        return results
    
    def test_endpoint_security(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Test individual endpoint security."""
        path = endpoint["path"]
        method = endpoint["method"]
        expected_auth = endpoint["expected_auth"]
        
        result = {
            "endpoint": path,
            "method": method,
            "expected_auth": expected_auth,
            "tests": {}
        }
        
        try:
            # Test without authentication
            response = self.make_request(method, path)
            result["tests"]["no_auth"] = {
                "status_code": response.status_code,
                "requires_auth": response.status_code == 401,
                "expected": expected_auth
            }
            
            # Test with invalid token
            headers = {"Authorization": "Bearer invalid_token"}
            response = self.make_request(method, path, headers=headers)
            result["tests"]["invalid_auth"] = {
                "status_code": response.status_code,
                "properly_rejects": response.status_code == 401
            }
            
            # Test for SQL injection vulnerabilities
            if method == "POST":
                malicious_data = {
                    "email": "test'; DROP TABLE users; --",
                    "password": "password",
                    "message": "'; SELECT * FROM users; --"
                }
                response = self.make_request(method, path, json=malicious_data)
                result["tests"]["sql_injection"] = {
                    "status_code": response.status_code,
                    "properly_handled": response.status_code in [400, 422, 500]
                }
            
            # Test for XSS vulnerabilities
            if method == "POST":
                xss_data = {
                    "message": "<script>alert('XSS')</script>",
                    "name": "<img src=x onerror=alert('XSS')>"
                }
                response = self.make_request(method, path, json=xss_data)
                result["tests"]["xss_protection"] = {
                    "status_code": response.status_code,
                    "response_contains_script": "<script>" in response.text.lower()
                }
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def make_request(self, method: str, path: str, headers: Dict = None, 
                    json: Dict = None, timeout: int = 10) -> requests.Response:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{path}"
        
        try:
            if method.upper() == "GET":
                return requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                return requests.post(url, headers=headers, json=json, timeout=timeout)
            elif method.upper() == "PUT":
                return requests.put(url, headers=headers, json=json, timeout=timeout)
            elif method.upper() == "DELETE":
                return requests.delete(url, headers=headers, timeout=timeout)
        except requests.exceptions.RequestException as e:
            # Create a mock response for connection errors
            response = requests.Response()
            response.status_code = 0
            response._content = str(e).encode()
            return response
    
    def check_security_headers(self) -> Dict[str, Any]:
        """Check for important security headers."""
        logger.info("Checking security headers...")
        
        try:
            response = self.make_request("GET", "/")
            headers = response.headers
            
            security_headers = {
                "X-Content-Type-Options": headers.get("X-Content-Type-Options"),
                "X-Frame-Options": headers.get("X-Frame-Options"),
                "X-XSS-Protection": headers.get("X-XSS-Protection"),
                "Strict-Transport-Security": headers.get("Strict-Transport-Security"),
                "Content-Security-Policy": headers.get("Content-Security-Policy"),
                "Referrer-Policy": headers.get("Referrer-Policy"),
                "Permissions-Policy": headers.get("Permissions-Policy")
            }
            
            return {
                "headers_present": security_headers,
                "missing_headers": [k for k, v in security_headers.items() if v is None],
                "recommendations": self.get_security_header_recommendations(security_headers)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_security_header_recommendations(self, headers: Dict[str, str]) -> List[str]:
        """Get recommendations for security headers."""
        recommendations = []
        
        if not headers.get("X-Content-Type-Options"):
            recommendations.append("Add X-Content-Type-Options: nosniff header")
        
        if not headers.get("X-Frame-Options"):
            recommendations.append("Add X-Frame-Options: DENY or SAMEORIGIN header")
        
        if not headers.get("Content-Security-Policy"):
            recommendations.append("Implement Content Security Policy (CSP)")
        
        if not headers.get("Strict-Transport-Security"):
            recommendations.append("Add HSTS header for HTTPS enforcement")
        
        return recommendations
    
    def check_cors_configuration(self) -> Dict[str, Any]:
        """Check CORS configuration."""
        logger.info("Checking CORS configuration...")
        
        try:
            # Test CORS preflight
            headers = {
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
            
            response = requests.options(f"{self.base_url}/api/v1/auth/login", 
                                      headers=headers, timeout=10)
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
                "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials")
            }
            
            return {
                "cors_headers": cors_headers,
                "allows_any_origin": cors_headers.get("Access-Control-Allow-Origin") == "*",
                "allows_credentials": cors_headers.get("Access-Control-Allow-Credentials") == "true",
                "security_risk": (cors_headers.get("Access-Control-Allow-Origin") == "*" and 
                                cors_headers.get("Access-Control-Allow-Credentials") == "true")
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def check_rate_limiting(self) -> Dict[str, Any]:
        """Check rate limiting implementation."""
        logger.info("Checking rate limiting...")
        
        try:
            # Make multiple rapid requests
            responses = []
            for i in range(10):
                response = self.make_request("GET", "/api/v1/health")
                responses.append({
                    "request_number": i + 1,
                    "status_code": response.status_code,
                    "rate_limit_headers": {
                        "X-RateLimit-Limit": response.headers.get("X-RateLimit-Limit"),
                        "X-RateLimit-Remaining": response.headers.get("X-RateLimit-Remaining"),
                        "X-RateLimit-Reset": response.headers.get("X-RateLimit-Reset"),
                        "Retry-After": response.headers.get("Retry-After")
                    }
                })
                
                if response.status_code == 429:
                    break
            
            rate_limited = any(r["status_code"] == 429 for r in responses)
            
            return {
                "responses": responses,
                "rate_limiting_active": rate_limited,
                "rate_limit_headers_present": any(
                    r["rate_limit_headers"]["X-RateLimit-Limit"] for r in responses
                )
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def audit_authentication(self) -> Dict[str, Any]:
        """Audit authentication mechanisms."""
        logger.info("Auditing authentication...")
        
        results = {
            "password_policy": self.check_password_policy(),
            "token_security": self.check_token_security(),
            "session_management": self.check_session_management(),
            "brute_force_protection": self.check_brute_force_protection()
        }
        
        return results
    
    def check_password_policy(self) -> Dict[str, Any]:
        """Check password policy enforcement."""
        weak_passwords = [
            "123456",
            "password",
            "123",
            "abc",
            "test"
        ]
        
        results = []
        
        for weak_password in weak_passwords:
            try:
                data = {
                    "email": f"test_{int(time.time())}@example.com",
                    "password": weak_password,
                    "name": "Test User"
                }
                
                response = self.make_request("POST", "/api/v1/auth/register", json=data)
                
                results.append({
                    "password": weak_password,
                    "status_code": response.status_code,
                    "rejected": response.status_code in [400, 422]
                })
                
            except Exception as e:
                results.append({
                    "password": weak_password,
                    "error": str(e)
                })
        
        return {
            "weak_password_tests": results,
            "properly_rejects_weak_passwords": all(
                r.get("rejected", False) for r in results if "error" not in r
            )
        }
    
    def check_token_security(self) -> Dict[str, Any]:
        """Check JWT token security."""
        # This would require analyzing the JWT implementation
        # For now, return basic checks
        return {
            "jwt_algorithm": "Check if using secure algorithm (RS256/ES256)",
            "token_expiration": "Check if tokens have reasonable expiration",
            "refresh_token_rotation": "Check if refresh tokens are rotated",
            "token_blacklisting": "Check if token blacklisting is implemented"
        }
    
    def check_session_management(self) -> Dict[str, Any]:
        """Check session management security."""
        return {
            "session_timeout": "Check if sessions timeout appropriately",
            "concurrent_sessions": "Check concurrent session handling",
            "session_invalidation": "Check if sessions are invalidated on logout"
        }
    
    def check_brute_force_protection(self) -> Dict[str, Any]:
        """Check brute force protection."""
        # Test multiple failed login attempts
        results = []
        
        for i in range(5):
            try:
                data = {
                    "email": "nonexistent@example.com",
                    "password": f"wrong_password_{i}"
                }
                
                response = self.make_request("POST", "/api/v1/auth/login", json=data)
                
                results.append({
                    "attempt": i + 1,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0
                })
                
            except Exception as e:
                results.append({
                    "attempt": i + 1,
                    "error": str(e)
                })
        
        return {
            "failed_login_attempts": results,
            "account_lockout_detected": any(r.get("status_code") == 429 for r in results),
            "response_time_increases": self.check_response_time_pattern(results)
        }
    
    def check_response_time_pattern(self, results: List[Dict]) -> bool:
        """Check if response times increase with failed attempts (rate limiting)."""
        times = [r.get("response_time", 0) for r in results if "error" not in r]
        if len(times) < 3:
            return False
        
        # Check if response times generally increase
        increases = sum(1 for i in range(1, len(times)) if times[i] > times[i-1])
        return increases >= len(times) // 2
    
    def audit_input_validation(self) -> Dict[str, Any]:
        """Audit input validation and sanitization."""
        logger.info("Auditing input validation...")
        
        return {
            "sql_injection_protection": self.test_sql_injection(),
            "xss_protection": self.test_xss_protection(),
            "command_injection_protection": self.test_command_injection(),
            "file_upload_security": self.test_file_upload_security(),
            "data_validation": self.test_data_validation()
        }
    
    def test_sql_injection(self) -> Dict[str, Any]:
        """Test SQL injection protection."""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --",
            "' UNION SELECT * FROM users --"
        ]
        
        results = []
        
        for payload in sql_payloads:
            try:
                data = {
                    "email": payload,
                    "password": "password"
                }
                
                response = self.make_request("POST", "/api/v1/auth/login", json=data)
                
                results.append({
                    "payload": payload,
                    "status_code": response.status_code,
                    "properly_handled": response.status_code in [400, 422, 401]
                })
                
            except Exception as e:
                results.append({
                    "payload": payload,
                    "error": str(e)
                })
        
        return {
            "sql_injection_tests": results,
            "protection_effective": all(
                r.get("properly_handled", False) for r in results if "error" not in r
            )
        }
    
    def test_xss_protection(self) -> Dict[str, Any]:
        """Test XSS protection."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>"
        ]
        
        results = []
        
        for payload in xss_payloads:
            try:
                data = {
                    "message": payload,
                    "name": payload
                }
                
                response = self.make_request("POST", "/api/v1/chat/message", json=data)
                
                results.append({
                    "payload": payload,
                    "status_code": response.status_code,
                    "response_contains_payload": payload.lower() in response.text.lower(),
                    "properly_sanitized": payload.lower() not in response.text.lower()
                })
                
            except Exception as e:
                results.append({
                    "payload": payload,
                    "error": str(e)
                })
        
        return {
            "xss_tests": results,
            "protection_effective": all(
                r.get("properly_sanitized", False) for r in results if "error" not in r
            )
        }
    
    def test_command_injection(self) -> Dict[str, Any]:
        """Test command injection protection."""
        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`"
        ]
        
        results = []
        
        for payload in command_payloads:
            try:
                data = {
                    "message": payload,
                    "filename": payload
                }
                
                response = self.make_request("POST", "/api/v1/chat/message", json=data)
                
                results.append({
                    "payload": payload,
                    "status_code": response.status_code,
                    "properly_handled": response.status_code in [400, 422]
                })
                
            except Exception as e:
                results.append({
                    "payload": payload,
                    "error": str(e)
                })
        
        return {
            "command_injection_tests": results,
            "protection_effective": all(
                r.get("properly_handled", False) for r in results if "error" not in r
            )
        }
    
    def test_file_upload_security(self) -> Dict[str, Any]:
        """Test file upload security."""
        # This would test file upload endpoints if they exist
        return {
            "file_type_validation": "Check if file types are validated",
            "file_size_limits": "Check if file size limits are enforced",
            "malicious_file_detection": "Check if malicious files are detected",
            "file_storage_security": "Check if uploaded files are stored securely"
        }
    
    def test_data_validation(self) -> Dict[str, Any]:
        """Test general data validation."""
        invalid_data_tests = [
            {
                "endpoint": "/api/v1/auth/register",
                "data": {"email": "invalid-email", "password": "123"},
                "expected_status": [400, 422]
            },
            {
                "endpoint": "/api/v1/auth/login",
                "data": {"email": "", "password": ""},
                "expected_status": [400, 422]
            }
        ]
        
        results = []
        
        for test in invalid_data_tests:
            try:
                response = self.make_request("POST", test["endpoint"], json=test["data"])
                
                results.append({
                    "endpoint": test["endpoint"],
                    "data": test["data"],
                    "status_code": response.status_code,
                    "properly_validated": response.status_code in test["expected_status"]
                })
                
            except Exception as e:
                results.append({
                    "endpoint": test["endpoint"],
                    "error": str(e)
                })
        
        return {
            "validation_tests": results,
            "validation_effective": all(
                r.get("properly_validated", False) for r in results if "error" not in r
            )
        }
    
    def audit_gdpr_compliance(self) -> Dict[str, Any]:
        """Audit GDPR compliance."""
        logger.info("Auditing GDPR compliance...")
        
        return {
            "data_collection": self.check_data_collection_practices(),
            "consent_management": self.check_consent_management(),
            "data_access_rights": self.check_data_access_rights(),
            "data_deletion_rights": self.check_data_deletion_rights(),
            "data_portability": self.check_data_portability(),
            "privacy_policy": self.check_privacy_policy(),
            "data_breach_procedures": self.check_data_breach_procedures()
        }
    
    def check_data_collection_practices(self) -> Dict[str, Any]:
        """Check data collection practices."""
        return {
            "minimal_data_collection": "Check if only necessary data is collected",
            "purpose_limitation": "Check if data is collected for specific purposes",
            "data_retention_policy": "Check if data retention policies are defined",
            "lawful_basis": "Check if lawful basis for processing is established"
        }
    
    def check_consent_management(self) -> Dict[str, Any]:
        """Check consent management."""
        return {
            "explicit_consent": "Check if explicit consent is obtained",
            "consent_withdrawal": "Check if users can withdraw consent",
            "consent_records": "Check if consent records are maintained",
            "granular_consent": "Check if granular consent options are provided"
        }
    
    def check_data_access_rights(self) -> Dict[str, Any]:
        """Check data access rights (Right to Access)."""
        return {
            "data_export_endpoint": "Check if users can export their data",
            "data_visibility": "Check if users can view their stored data",
            "response_timeframe": "Check if requests are handled within 30 days"
        }
    
    def check_data_deletion_rights(self) -> Dict[str, Any]:
        """Check data deletion rights (Right to be Forgotten)."""
        return {
            "account_deletion": "Check if users can delete their accounts",
            "data_anonymization": "Check if data is properly anonymized",
            "deletion_confirmation": "Check if deletion is confirmed to users",
            "retention_exceptions": "Check if legal retention requirements are handled"
        }
    
    def check_data_portability(self) -> Dict[str, Any]:
        """Check data portability rights."""
        return {
            "data_export_format": "Check if data is exportable in standard formats",
            "complete_data_export": "Check if all user data is included in exports",
            "automated_export": "Check if export process is automated"
        }
    
    def check_privacy_policy(self) -> Dict[str, Any]:
        """Check privacy policy compliance."""
        return {
            "policy_accessibility": "Check if privacy policy is easily accessible",
            "policy_completeness": "Check if policy covers all required elements",
            "policy_updates": "Check if policy update procedures are defined",
            "plain_language": "Check if policy is written in plain language"
        }
    
    def check_data_breach_procedures(self) -> Dict[str, Any]:
        """Check data breach procedures."""
        return {
            "breach_detection": "Check if breach detection mechanisms exist",
            "notification_procedures": "Check if notification procedures are defined",
            "authority_reporting": "Check if authority reporting is implemented",
            "user_notification": "Check if user notification procedures exist"
        }
    
    def audit_code_security(self) -> Dict[str, Any]:
        """Audit code-level security."""
        logger.info("Auditing code security...")
        
        backend_path = Path(__file__).parent.parent
        
        return {
            "dependency_vulnerabilities": self.check_dependency_vulnerabilities(backend_path),
            "secret_management": self.check_secret_management(backend_path),
            "logging_security": self.check_logging_security(backend_path),
            "error_handling": self.check_error_handling(backend_path)
        }
    
    def check_dependency_vulnerabilities(self, backend_path: Path) -> Dict[str, Any]:
        """Check for dependency vulnerabilities."""
        requirements_files = [
            backend_path / "requirements.txt",
            backend_path / "pyproject.toml"
        ]
        
        found_files = [f for f in requirements_files if f.exists()]
        
        return {
            "requirements_files_found": [str(f) for f in found_files],
            "recommendation": "Run 'pip audit' or 'safety check' to scan for vulnerabilities",
            "automated_scanning": "Consider integrating dependency scanning in CI/CD"
        }
    
    def check_secret_management(self, backend_path: Path) -> Dict[str, Any]:
        """Check secret management practices."""
        potential_secrets = []
        
        # Common patterns for secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        # Check Python files for hardcoded secrets
        for py_file in backend_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in secret_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        potential_secrets.append({
                            "file": str(py_file.relative_to(backend_path)),
                            "pattern": pattern,
                            "matches": len(matches)
                        })
            except Exception:
                continue
        
        return {
            "potential_hardcoded_secrets": potential_secrets,
            "env_file_usage": (backend_path / ".env").exists(),
            "recommendation": "Use environment variables or secret management systems"
        }
    
    def check_logging_security(self, backend_path: Path) -> Dict[str, Any]:
        """Check logging security practices."""
        return {
            "sensitive_data_logging": "Check if sensitive data is logged",
            "log_injection_protection": "Check if log injection is prevented",
            "log_access_control": "Check if log access is controlled",
            "log_retention_policy": "Check if log retention policies exist"
        }
    
    def check_error_handling(self, backend_path: Path) -> Dict[str, Any]:
        """Check error handling security."""
        return {
            "information_disclosure": "Check if errors disclose sensitive information",
            "generic_error_messages": "Check if generic error messages are used",
            "error_logging": "Check if errors are properly logged",
            "exception_handling": "Check if exceptions are properly handled"
        }
    
    def audit_configuration_security(self) -> Dict[str, Any]:
        """Audit configuration security."""
        logger.info("Auditing configuration security...")
        
        return {
            "database_security": self.check_database_security(),
            "server_configuration": self.check_server_configuration(),
            "environment_variables": self.check_environment_variables(),
            "deployment_security": self.check_deployment_security()
        }
    
    def check_database_security(self) -> Dict[str, Any]:
        """Check database security configuration."""
        return {
            "connection_encryption": "Check if database connections are encrypted",
            "access_controls": "Check if proper database access controls exist",
            "backup_security": "Check if database backups are secured",
            "audit_logging": "Check if database audit logging is enabled"
        }
    
    def check_server_configuration(self) -> Dict[str, Any]:
        """Check server configuration security."""
        return {
            "debug_mode": "Check if debug mode is disabled in production",
            "server_tokens": "Check if server version information is hidden",
            "unnecessary_services": "Check if unnecessary services are disabled",
            "firewall_configuration": "Check if firewall is properly configured"
        }
    
    def check_environment_variables(self) -> Dict[str, Any]:
        """Check environment variable security."""
        return {
            "sensitive_env_vars": "Check if sensitive data is in environment variables",
            "env_file_permissions": "Check if .env files have proper permissions",
            "env_var_validation": "Check if environment variables are validated"
        }
    
    def check_deployment_security(self) -> Dict[str, Any]:
        """Check deployment security."""
        return {
            "https_enforcement": "Check if HTTPS is enforced",
            "security_updates": "Check if security updates are applied",
            "monitoring_alerting": "Check if security monitoring is in place",
            "backup_procedures": "Check if secure backup procedures exist"
        }
    
    def generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on audit results."""
        recommendations = []
        
        # API Security recommendations
        api_results = self.audit_results.get("api_security", {})
        if api_results.get("security_headers", {}).get("missing_headers"):
            recommendations.append("Implement missing security headers")
        
        if api_results.get("cors_configuration", {}).get("security_risk"):
            recommendations.append("Fix CORS configuration security risk")
        
        if not api_results.get("rate_limiting", {}).get("rate_limiting_active"):
            recommendations.append("Implement rate limiting")
        
        # Authentication recommendations
        auth_results = self.audit_results.get("authentication", {})
        if not auth_results.get("password_policy", {}).get("properly_rejects_weak_passwords"):
            recommendations.append("Strengthen password policy enforcement")
        
        if not auth_results.get("brute_force_protection", {}).get("account_lockout_detected"):
            recommendations.append("Implement brute force protection")
        
        # Input validation recommendations
        input_results = self.audit_results.get("input_validation", {})
        if not input_results.get("sql_injection_protection", {}).get("protection_effective"):
            recommendations.append("Improve SQL injection protection")
        
        if not input_results.get("xss_protection", {}).get("protection_effective"):
            recommendations.append("Implement XSS protection")
        
        # Code security recommendations
        code_results = self.audit_results.get("code_security", {})
        if code_results.get("secret_management", {}).get("potential_hardcoded_secrets"):
            recommendations.append("Remove hardcoded secrets from code")
        
        # General recommendations
        recommendations.extend([
            "Implement comprehensive logging and monitoring",
            "Regular security testing and code reviews",
            "Keep dependencies updated",
            "Implement security headers",
            "Use HTTPS everywhere",
            "Regular security training for developers"
        ])
        
        return recommendations
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Run complete security audit."""
        logger.info("Starting comprehensive security audit...")
        
        self.audit_results["api_security"] = self.audit_api_endpoints()
        self.audit_results["authentication"] = self.audit_authentication()
        self.audit_results["input_validation"] = self.audit_input_validation()
        self.audit_results["gdpr_compliance"] = self.audit_gdpr_compliance()
        self.audit_results["code_security"] = self.audit_code_security()
        self.audit_results["configuration_security"] = self.audit_configuration_security()
        self.audit_results["recommendations"] = self.generate_recommendations()
        
        return self.audit_results
    
    def save_audit_report(self, filename: str = None):
        """Save audit report to file."""
        if not filename:
            timestamp = int(time.time())
            filename = f"security_audit_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), "..", "reports", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.audit_results, f, indent=2, default=str)
        
        logger.info(f"Security audit report saved to: {filepath}")
        return filepath
    
    def print_audit_summary(self):
        """Print audit summary."""
        print("\n" + "="*60)
        print("SECURITY AUDIT SUMMARY")
        print("="*60)
        
        # API Security Summary
        api_results = self.audit_results.get("api_security", {})
        endpoint_tests = api_results.get("endpoint_tests", [])
        successful_tests = sum(1 for test in endpoint_tests if "error" not in test)
        
        print(f"API Endpoints Tested: {len(endpoint_tests)}")
        print(f"Successful Tests: {successful_tests}")
        
        # Security Headers
        missing_headers = api_results.get("security_headers", {}).get("missing_headers", [])
        print(f"Missing Security Headers: {len(missing_headers)}")
        
        # Rate Limiting
        rate_limiting = api_results.get("rate_limiting", {}).get("rate_limiting_active", False)
        print(f"Rate Limiting Active: {'Yes' if rate_limiting else 'No'}")
        
        # Authentication
        auth_results = self.audit_results.get("authentication", {})
        password_policy = auth_results.get("password_policy", {}).get("properly_rejects_weak_passwords", False)
        print(f"Strong Password Policy: {'Yes' if password_policy else 'No'}")
        
        # Input Validation
        input_results = self.audit_results.get("input_validation", {})
        sql_protection = input_results.get("sql_injection_protection", {}).get("protection_effective", False)
        xss_protection = input_results.get("xss_protection", {}).get("protection_effective", False)
        print(f"SQL Injection Protection: {'Yes' if sql_protection else 'No'}")
        print(f"XSS Protection: {'Yes' if xss_protection else 'No'}")
        
        # Code Security
        code_results = self.audit_results.get("code_security", {})
        hardcoded_secrets = len(code_results.get("secret_management", {}).get("potential_hardcoded_secrets", []))
        print(f"Potential Hardcoded Secrets: {hardcoded_secrets}")
        
        # Recommendations
        recommendations = self.audit_results.get("recommendations", [])
        print(f"\nTotal Recommendations: {len(recommendations)}")
        
        print("\nTop Recommendations:")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"  {i}. {rec}")


def main():
    """Main function to run security audit."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Audit for Ponder API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--save", help="Save report to specific file")
    
    args = parser.parse_args()
    
    auditor = SecurityAuditor(args.url)
    
    try:
        audit_results = auditor.run_full_audit()
        
        auditor.print_audit_summary()
        
        if args.save:
            report_path = auditor.save_audit_report(args.save)
        else:
            report_path = auditor.save_audit_report()
        
        print(f"\nFull security audit report saved to: {report_path}")
        
    except KeyboardInterrupt:
        logger.info("Security audit interrupted by user")
    except Exception as e:
        logger.error(f"Security audit failed: {e}")


if __name__ == "__main__":
    main()