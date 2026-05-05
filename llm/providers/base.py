"""Provider interface for Large Language Model backends."""
from abc import ABC, abstractmethod

from llm.models import LLMRequest, LLMResponse


class LLMProvider(ABC):
    """Abstract interface all LLM providers must implement."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier."""

    @property
    def supports_json_mode(self) -> bool:
        """Whether this provider supports response_mime_type=application/json."""
        return False

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate one assistant response from a normalized request."""
