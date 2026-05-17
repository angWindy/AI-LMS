"""
Application Settings using Pydantic BaseSettings.
All configuration values can be overridden via environment variables.
"""
from typing import List, Any, Union
from pydantic import field_validator
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
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "postgresql://lms_user:lms_password@localhost:5432/lms_db"

    # CORS - Can be comma-separated string or list
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000"

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

    # LLM / Chatbot Configuration
    # Supported Google models:
    # - gemini-3.1-flash-lite (default, supports LLM_THINKING_LEVEL)
    # - gemini-2.5-flash-lite (supports LLM_THINKING_LEVEL)
    # - gemini-2.5-flash (supports LLM_THINKING_LEVEL)
    # - gemma-4-31b-it (no LLM_THINKING_LEVEL)
    LLM_PROVIDER: str = "google"
    LLM_MODEL: str = "gemini-3.1-flash-lite"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_OUTPUT_TOKENS: int = 512
    LLM_THINKING_LEVEL: str | None = None
    LLM_REQUEST_TIMEOUT_SECONDS: int = 180
    GOOGLE_AI_API_KEY: str | None = None
    GOOGLE_AI_ENDPOINT: str = "https://generativelanguage.googleapis.com/v1beta"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS_ORIGINS from comma-separated string to list."""
        if isinstance(v, str):
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return ["http://localhost:3000"]

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS


settings = Settings()
