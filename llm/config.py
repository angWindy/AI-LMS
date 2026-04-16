"""Configuration for LLM providers."""
from dataclasses import dataclass
import os


@dataclass
class LLMConfig:
    """Runtime configuration for LLM providers."""

    provider: str = "google"
    model: str = "gemini-2.5-flash"
    temperature: float = 0.1
    max_output_tokens: int = 512
    thinking_level: str | None = None
    google_api_key: str | None = None

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Build configuration from environment variables."""
        return cls(
            provider=os.getenv("LLM_PROVIDER", "google"),
            model=os.getenv("LLM_MODEL", "gemini-2.5-flash"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            max_output_tokens=int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "512")),
            thinking_level=os.getenv("LLM_THINKING_LEVEL"),
            google_api_key=os.getenv("GOOGLE_AI_API_KEY"),
        )
