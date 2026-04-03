from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field, ConfigDict
from typing import List, Dict, Optional, Any
from typing_extensions import TypedDict
from datetime import timedelta
from pathlib import Path
import os
from dotenv import load_dotenv
from pydantic import field_validator

# Load the appropriate .env file based on environment
# Look for .env files in the project root (parent of backend directory)
project_root = Path(__file__).parent.parent.parent.parent
# env_file = project_root / (".env.development" if os.getenv("ENVIRONMENT") != "production" else ".env.production")
# if env_file.exists():
#     load_dotenv(env_file)

default_env_file = project_root / ".env"
load_dotenv(default_env_file)

class UserSettings(TypedDict):
    learning_levels: List[str]
    time_zones: List[str]
    languages: List[str]

class LearningPlanSettings(TypedDict):
    min_steps: int
    max_steps: int
    required_sections: List[str]
    time_formats: List[str]

class ProjectSettings(TypedDict):
    difficulty_levels: List[str]
    max_duration: timedelta
    min_milestones: int
    max_milestones: int

class ChatSettings(TypedDict):
    project_settings: ProjectSettings
    message_limit: int
    response_timeout: int

class EngagementThresholds(TypedDict):
    messages_per_day: float
    response_time: float
    session_duration: float
    active_streak: float
    completion_rate: float

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # "development" or "production"

    # Database settings
    DATABASE_URL: str = Field(default=os.getenv("DATABASE_URL", "sqlite:///./app.db"))
    DATABASE_BACKUP_DIR: str = Field(default=os.getenv("DATABASE_BACKUP_DIR", "./backups"))

    # Data Management
    MAX_BACKUP_COUNT: int = Field(default=int(os.getenv("MAX_BACKUP_COUNT", "5")))
    BACKUP_RETENTION_DAYS: int = Field(default=int(os.getenv("BACKUP_RETENTION_DAYS", "30")))
    ANALYTICS_EXPORT_DIR: str = Field(default=os.getenv("ANALYTICS_EXPORT_DIR", "./analytics"))

    # API Keys and Security
    OPENAI_API_KEY: str = Field(default=os.getenv("OPENAI_API_KEY", ""))
    DEEPSEEK_API_KEY: str = Field(default=os.getenv("DEEPSEEK_API_KEY", ""))
    JWT_SECRET: str = Field(default=os.getenv("JWT_SECRET", ""))
    JWT_ALGORITHM: str = "HS256"
    ADMIN_API_KEY: str = Field(default=os.getenv("ADMIN_API_KEY", "dev-admin-key"))

    # Logging
    LOG_LEVEL: str = "INFO"  # Can be DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_TO_FILE: bool = True
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # AI Models
    GPT_MODEL: str = "gpt-4o-mini"
    GPT_MAX_TOKENS: int = 4000
    GPT_TEMPERATURE: float = 0.7

    # API Timeouts
    OPENAI_TIMEOUT: float = 30.0  # 30 seconds for standard OpenAI requests
    DEEPSEEK_TIMEOUT: float = 300.0  # 5 minutes for DeepSeek (reasoning model needs more time)
    FALLBACK_TIMEOUT: float = 20.0  # 20 seconds for fallback requests

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None
    EMAIL_USER: Optional[str] = None
  # SMTP / Email settings
    SMTP_USER: str = Field(default=os.getenv("SMTP_USER", ""))
    SMTP_PASS: str = Field(default=os.getenv("SMTP_PASS", ""))
    SMTP_FROM: str = Field(default=os.getenv("SMTP_FROM", ""))
    SMTP_SERVER: str = Field(default=os.getenv("SMTP_SERVER", "smtp.gmail.com"))
    SMTP_PORT: int = Field(default=int(os.getenv("SMTP_PORT", 587)))
    SMTP_TLS: bool = Field(default=True)      
    SMTP_SSL: bool = Field(default=False) 

    # Website URL
    WEBSITE_URL: str = Field(default=os.getenv("WEBSITE_URL"))

    # Alternative Models
    ALTERNATIVE_MODELS: Dict[str, Dict[str, Any]] = Field(default={
        "deepseek-reasoner": {
            "provider": "deepseek",
            "api_key_env": "DEEPSEEK_API_KEY",
            "model_name": "deepseek-reasoner",
            "max_tokens": 10000,
            "temperature": 0.7,
            "description": "DeepSeek R1 - Advanced reasoning model"
        },
        "claude-3-opus": {
            "provider": "anthropic",
            "api_url": "https://api.anthropic.com/v1/messages",
            "api_key_env": "ANTHROPIC_API_KEY",
            "max_tokens": 4096,
            "temperature": 0.7,
            "description": "Claude 3 Opus - High quality educational content"
        },
        "grok-3": {
            "provider": "xai",
            "api_url": "https://api.xai.com/v1/chat/completions",
            "api_key_env": "XAI_API_KEY",
            "max_tokens": 4096,
            "temperature": 0.7,
            "description": "Grok 3 - Creative and engaging educational content"
        },
        "llama-3-70b": {
            "provider": "together",
            "api_url": "https://api.together.xyz/v1/completions",
            "api_key_env": "TOGETHER_API_KEY",
            "max_tokens": 4096,
            "temperature": 0.7,
            "description": "Llama 3 70B - Open source model for education"
        },
        "mistral-large": {
            "provider": "mistral",
            "api_url": "https://api.mistral.ai/v1/chat/completions",
            "api_key_env": "MISTRAL_API_KEY",
            "max_tokens": 4096,
            "temperature": 0.7,
            "description": "Mistral Large - Efficient and cost-effective educational content"
        }
    })

    # Currently active model
    ACTIVE_MODEL: str = Field(default=os.getenv("ACTIVE_MODEL", "gpt-o1-mini"))

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # CORS Settings
    CORS_ORIGINS: List[str] = []
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, value):
        if isinstance(value, str):
            return [v.strip() for v in value.split(",")]
        return value
    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour in seconds
    MAX_CACHE_ITEMS: int = 10000

    # Project Settings
    PROJECT_TEMPLATES_PATH: str = str(Path(__file__).parent / "data" / "project_templates.json")

    # Career Paths
    CAREER_PATHS: Dict[str, str] = Field(default={
        'software_development': 'coding mentor',
        'data_science': 'data science mentor',
        'digital_marketing': 'digital marketing strategist',
        'design': 'design mentor',
        'business': 'business strategy mentor',
        'content_creation': 'content strategy mentor',
        'finance': 'financial planning mentor',
        'healthcare': 'healthcare mentor',
        'education': 'education specialist',
        'arts': 'creative arts mentor',
        'music': 'music instructor',
        'writing': 'writing coach',
        'fitness': 'fitness trainer',
        'culinary': 'culinary expert'
    })

    # User Settings
    USER_SETTINGS: UserSettings = Field(default={
        'learning_levels': ['beginner', 'intermediate', 'advanced', 'expert'],
        'time_zones': ['UTC', 'UTC+1', 'UTC-1'],
        'languages': ['en', 'es', 'fr', 'de']
    })

    # Learning Plan Settings
    LEARNING_PLAN_SETTINGS: LearningPlanSettings = Field(default={
        'min_steps': 3,
        'max_steps': 7,
        'required_sections': [
            'prerequisites',
            'learning objectives',
            'resources',
            'practice exercises',
            'assessment criteria'
        ],
        'time_formats': ['hour', 'day', 'week', 'month']
    })

    # Chat Settings
    CHAT_SETTINGS: ChatSettings = Field(default={
        'project_settings': {
            'difficulty_levels': ['beginner', 'intermediate', 'advanced', 'expert'],
            'max_duration': timedelta(days=30),
            'min_milestones': 3,
            'max_milestones': 10
        },
        'message_limit': 100,
        'response_timeout': 60
    })

    # Engagement Settings
    ENGAGEMENT_THRESHOLDS: EngagementThresholds = Field(default={
        'messages_per_day': 5.0,
        'response_time': 300.0,  # 5 minutes
        'session_duration': 600.0,  # 10 minutes
        'active_streak': 3.0,  # days
        'completion_rate': 0.7
    })

    # Learning Settings
    LEARNING_PACE_BASELINE: float = Field(default=1.0)

    # Vector Database Settings
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")  # Only needed in production
    PINECONE_ENV: str = os.getenv("PINECONE_ENV", "gcp-starter")  # Only needed in production

    # Vector Store Settings
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    VECTOR_STORE_TYPE: str = Field(default=os.getenv("VECTOR_STORE_TYPE", "qdrant"))

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def should_reset_db(self) -> bool:
        return self.is_development and os.getenv("RESET_DB", "").lower() == "true"

    model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=True,
    extra="allow"
)

    @field_validator("DATABASE_URL", "OPENAI_API_KEY", "JWT_SECRET")
    @classmethod
    def validate_required(cls, v: Optional[str], info) -> str:
        if not v:
            raise ValueError(f"{info.field_name} is required")
        return v

    @field_validator("RATE_LIMIT_PER_MINUTE")
    @classmethod
    def validate_rate_limit(cls, v: int, info) -> int:
        if v < 1:
            raise ValueError("Rate limit must be at least 1 per minute")
        return v

settings = Settings()