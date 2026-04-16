"""Factory utilities for selecting active LLM provider."""

from llm.config import LLMConfig
from llm.providers.base import LLMProvider
from llm.providers.google_gemini import GoogleGeminiProvider
from llm.providers.mock import MockLLMProvider


def get_llm_provider(config: LLMConfig) -> LLMProvider:
    """Return provider instance based on configuration."""
    provider = config.provider.lower().strip()
    if provider == "google":
        return GoogleGeminiProvider(config)
    if provider == "mock":
        return MockLLMProvider(config)

    raise ValueError(
        f"Unsupported LLM_PROVIDER '{config.provider}'. "
        "Supported values: google, mock"
    )
