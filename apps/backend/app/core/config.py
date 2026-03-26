"""
Application Settings using Pydantic BaseSettings.
All configuration values can be overridden via environment variables.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Project Info
    PROJECT_NAME: str = "LMS API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "postgresql://lms_user:lms_password@localhost:5432/lms_db"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # File Storage
    STORAGE_PATH: str = "./storage"
    MAX_VIDEO_SIZE_MB: int = 500
    MAX_DOCUMENT_SIZE_MB: int = 50
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/webm", "video/quicktime"]
    ALLOWED_DOCUMENT_TYPES: List[str] = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    # First Admin User (created on startup if not exists)
    FIRST_ADMIN_EMAIL: str = "admin@lms.local"
    FIRST_ADMIN_PASSWORD: str = "changeme123"


settings = Settings()
