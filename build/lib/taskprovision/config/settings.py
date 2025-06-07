"""
TaskProvision configuration management
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # App configuration
    app_name: str = "TaskProvision"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = Field(default="development", env="ENVIRONMENT")

    # Server configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")

    # Database configuration
    database_url: str = Field(
        default="postgresql://taskprovision:password@localhost/taskprovision",
        env="DATABASE_URL"
    )
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # AI Services
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:1.5b", env="OLLAMA_MODEL")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")

    # External Services
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    stripe_api_key: Optional[str] = Field(default=None, env="STRIPE_API_KEY")
    stripe_webhook_secret: Optional[str] = Field(default=None, env="STRIPE_WEBHOOK_SECRET")

    # Email configuration
    smtp_host: str = Field(default="localhost", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")

    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # File storage
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: List[str] = Field(
        default=["py", "js", "ts", "go", "rs", "java", "cpp", "c", "h"],
        env="ALLOWED_FILE_TYPES"
    )

    # Task management
    default_task_timeout: int = Field(default=300, env="DEFAULT_TASK_TIMEOUT")  # 5 minutes
    max_concurrent_tasks: int = Field(default=10, env="MAX_CONCURRENT_TASKS")

    # Code generation
    code_generation_timeout: int = Field(default=60, env="CODE_GENERATION_TIMEOUT")
    max_code_length: int = Field(default=10000, env="MAX_CODE_LENGTH")

    # Quality guard
    quality_check_enabled: bool = Field(default=True, env="QUALITY_CHECK_ENABLED")
    max_function_length: int = Field(default=50, env="MAX_FUNCTION_LENGTH")
    max_complexity: int = Field(default=10, env="MAX_COMPLEXITY")

    # Sales automation
    lead_generation_enabled: bool = Field(default=True, env="LEAD_GENERATION_ENABLED")
    github_mining_enabled: bool = Field(default=True, env="GITHUB_MINING_ENABLED")
    email_campaigns_enabled: bool = Field(default=True, env="EMAIL_CAMPAIGNS_ENABLED")

    # API rate limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    burst_limit: int = Field(default=10, env="BURST_LIMIT")

    # Cors settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def get_database_url() -> str:
    """Get database URL for SQLAlchemy"""
    settings = get_settings()
    return settings.database_url


def get_redis_url() -> str:
    """Get Redis URL"""
    settings = get_settings()
    return settings.redis_url


def is_production() -> bool:
    """Check if running in production environment"""
    settings = get_settings()
    return settings.environment.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment"""
    settings = get_settings()
    return settings.environment.lower() == "development"


def get_upload_settings() -> dict:
    """Get file upload settings"""
    settings = get_settings()
    return {
        "upload_dir": settings.upload_dir,
        "max_file_size": settings.max_file_size,
        "allowed_file_types": settings.allowed_file_types,
    }


def get_ai_settings() -> dict:
    """Get AI service settings"""
    settings = get_settings()
    return {
        "ollama_base_url": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
        "openai_api_key": settings.openai_api_key,
        "anthropic_api_key": settings.anthropic_api_key,
    }


def get_quality_settings() -> dict:
    """Get quality guard settings"""
    settings = get_settings()
    return {
        "enabled": settings.quality_check_enabled,
        "max_function_length": settings.max_function_length,
        "max_complexity": settings.max_complexity,
        "timeout": settings.code_generation_timeout,
    }