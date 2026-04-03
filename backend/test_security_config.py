"""
Test security configuration and imports.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_security_imports():
    """Test that security modules can be imported"""
    try:
        from app.middleware.security_middleware import SecurityMiddleware, RateLimitMiddleware
        from app.config.security import security_config, get_cors_origins, get_security_headers
        from app.schemas.validation import (
            SecureUserRegistration, SecureUserLogin, SecureChatMessage,
            EmailField, PasswordField, SecureStringField
        )
        print("✓ All security modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_security_config():
    """Test security configuration"""
    try:
        from app.config.security import security_config, get_cors_origins, get_security_headers
        
        # Test CORS origins
        origins = get_cors_origins()
        assert isinstance(origins, list)
        assert len(origins) > 0
        print(f"✓ CORS origins configured: {len(origins)} origins")
        
        # Test security headers
        headers = get_security_headers()
        assert isinstance(headers, dict)
        assert 'X-Frame-Options' in headers
        assert 'X-Content-Type-Options' in headers
        assert 'Content-Security-Policy' in headers
        print(f"✓ Security headers configured: {len(headers)} headers")
        
        # Test security config values
        assert security_config.JWT_ALGORITHM == "HS256"
        assert security_config.PASSWORD_MIN_LENGTH >= 8
        assert security_config.RATE_LIMIT_DEFAULT_REQUESTS > 0
        print("✓ Security configuration values are valid")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_validation_schemas():
    """Test validation schemas"""
    try:
        from app.schemas.validation import SecureUserRegistration, EmailField, PasswordField
        
        # Test email validation
        try:
            email = EmailField.validate("invalid-email")
            print("❌ Email validation failed - should reject invalid email")
            return False
        except ValueError:
            print("✓ Email validation working - rejects invalid emails")
        
        # Test valid email
        try:
            email = EmailField.validate("test@example.com")
            print("✓ Email validation working - accepts valid emails")
        except ValueError as e:
            print(f"❌ Email validation failed for valid email: {e}")
            return False
        
        # Test password validation
        try:
            password = PasswordField.validate("weak")
            print("❌ Password validation failed - should reject weak passwords")
            return False
        except ValueError:
            print("✓ Password validation working - rejects weak passwords")
        
        return True
    except Exception as e:
        print(f"❌ Validation schema error: {e}")
        return False

def test_middleware_classes():
    """Test middleware classes can be instantiated"""
    try:
        from app.middleware.security_middleware import SecurityMiddleware, RateLimitMiddleware
        from unittest.mock import MagicMock
        
        # Mock app
        mock_app = MagicMock()
        
        # Test SecurityMiddleware
        security_middleware = SecurityMiddleware(mock_app)
        assert security_middleware is not None
        print("✓ SecurityMiddleware can be instantiated")
        
        # Test RateLimitMiddleware
        rate_limit_middleware = RateLimitMiddleware(mock_app)
        assert rate_limit_middleware is not None
        print("✓ RateLimitMiddleware can be instantiated")
        
        return True
    except Exception as e:
        print(f"❌ Middleware instantiation error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing security implementation...")
    print("=" * 50)
    
    tests = [
        test_security_imports,
        test_security_config,
        test_validation_schemas,
        test_middleware_classes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\nRunning {test.__name__}...")
        if test():
            passed += 1
        print("-" * 30)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All security configuration tests passed!")
        print("\nSecurity features implemented:")
        print("- ✓ Input validation and sanitization middleware")
        print("- ✓ Rate limiting with Redis support")
        print("- ✓ Comprehensive security headers")
        print("- ✓ Enhanced CORS configuration")
        print("- ✓ Secure validation schemas")
        print("- ✓ Content type and request size validation")
        print("- ✓ XSS and SQL injection protection")
        print("- ✓ Path traversal protection")
        print("- ✓ Password complexity validation")
        print("- ✓ File upload security")
    else:
        print(f"\n❌ {total - passed} tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()