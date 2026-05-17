"""Configuration for LLM providers."""
from dataclasses import dataclass
import os


@dataclass
class LLMConfig:
    """Runtime configuration for LLM providers."""

    provider: str = "google"
    model: str = "gemini-3.1-flash-lite"
    temperature: float = 0.1
    max_output_tokens: int = 512
    thinking_level: str | None = None
    request_timeout_seconds: int | None = 180
    google_api_key: str | None = None

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Build configuration from environment variables."""
        return cls(
            provider=os.getenv("LLM_PROVIDER", "google"),
            model=os.getenv("LLM_MODEL", "gemini-3.1-flash-lite"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            max_output_tokens=int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "512")),
            thinking_level=os.getenv("LLM_THINKING_LEVEL"),
            request_timeout_seconds=_get_int_or_none(
                os.getenv("LLM_REQUEST_TIMEOUT_SECONDS", "180")
            ),
            google_api_key=os.getenv("GOOGLE_AI_API_KEY"),
        )


def _get_int_or_none(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return int(value)
