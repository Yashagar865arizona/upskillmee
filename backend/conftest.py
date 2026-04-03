"""
Root-level conftest.py — sets required environment variables BEFORE any
application modules are imported.  This file is loaded by pytest before
tests/conftest.py and before any test module is collected.
"""
import os

# Set minimal env vars needed for settings.py to validate without a live
# infrastructure (real values are injected by CI).
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-tests-only")
os.environ.setdefault("WEBSITE_URL", "http://localhost:3000")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SMTP_FROM", "test@example.com")
os.environ.setdefault("SMTP_USER", "test@example.com")
os.environ.setdefault("SMTP_PASS", "test-smtp-password")
