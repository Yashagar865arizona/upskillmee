import os
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    """
    Load environment variables based on ENVIRONMENT value.
    Priority:
    1. Environment variables already set
    2. .env file
    3. .env.development or .env.production based on ENVIRONMENT
    """
    # Get the base directory (project root)
    base_dir = Path(__file__).parent.parent.parent.parent
    print(f"[DEBUG] Base dir: {base_dir}")

    # First try loading from .env
    env_file = base_dir / ".env"
    if env_file.exists():
        print(f"[DEBUG] Loading base .env from: {env_file}")
        load_dotenv(env_file)
    else:
        print("[DEBUG] .env file not found")

    # Get environment from ENV var or default to development
    env = os.getenv("ENVIRONMENT", "development")
    print(f"[DEBUG] ENVIRONMENT: {env}")

    # Load environment-specific file
    env_specific_file = base_dir / f".env.{env.lower()}"
    if env_specific_file.exists():
        print(f"[DEBUG] Loading environment-specific file: {env_specific_file}")
        load_dotenv(env_specific_file)
    else:
        print("[DEBUG] No environment-specific file found")

    # Print all required variables
    required_vars = ["DATABASE_URL", "OPENAI_API_KEY", "JWT_SECRET"]
    for var in required_vars:
        print(f"[DEBUG] {var} = {os.getenv(var)}")

    # Check if any are missing
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    return env
