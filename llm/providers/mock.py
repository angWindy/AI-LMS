"""Mock LLM provider for local fallback/testing without external APIs."""

from llm.config import LLMConfig
from llm.models import LLMRequest, LLMResponse
from llm.providers.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """A deterministic provider useful for development and tests."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    @property
    def provider_name(self) -> str:
        return "mock"

    def generate(self, request: LLMRequest) -> LLMResponse:
        latest_question = request.messages[-1].content if request.messages else ""
        return LLMResponse(
            text=f"[MOCK RESPONSE] You asked: {latest_question}",
            provider=self.provider_name,
            model="mock-v1",
            finish_reason="stop",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            raw={"mock": True},
        )
