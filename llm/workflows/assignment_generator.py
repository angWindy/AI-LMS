"""Workflow for generating assignment questions with an LLM."""
from dataclasses import dataclass

from llm.config import LLMConfig
from llm.models import ChatMessage, LLMRequest
from llm.prompts.assignment_generator import build_assignment_generator_prompt
from llm.providers.base import LLMProvider
from llm.providers.factory import get_llm_provider


@dataclass
class AssignmentGeneratorResult:
    """Raw LLM result for assignment generation."""

    text: str
    provider: str
    model: str
    finish_reason: str | None
    usage: dict[str, int] | None


class AssignmentGeneratorWorkflow:
    """Run assignment generation prompts against the configured provider."""

    def __init__(
        self,
        config: LLMConfig,
        provider: LLMProvider | None = None,
    ) -> None:
        self.config = config
        self.provider = provider or get_llm_provider(config)

    def run(
        self,
        question_count: int,
        course_context: str,
        lesson_context: str,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        thinking_level: str | None = None,
    ) -> AssignmentGeneratorResult:
        """Generate quiz content in JSON text format."""
        system_prompt = build_assignment_generator_prompt(
            question_count=question_count,
            course_context=course_context,
            lesson_context=lesson_context,
        )
        token_budget = max_output_tokens
        if token_budget is None:
            # Assignment JSON with 5+ questions can easily exceed 512 output tokens.
            token_budget = min(max(self.config.max_output_tokens, question_count * 650, 3000), 8192)

        request = LLMRequest(
            messages=[
                ChatMessage(
                    role="user",
                    content=(
                        "Generate the assignment JSON now with the required format."
                    ),
                )
            ],
            system_prompt=system_prompt,
            temperature=self.config.temperature if temperature is None else temperature,
            max_output_tokens=token_budget,
            thinking_level=(
                self.config.thinking_level if thinking_level is None else thinking_level
            ),
            metadata={"response_mime_type": "application/json"},
        )

        response = self.provider.generate(request)

        return AssignmentGeneratorResult(
            text=response.text,
            provider=response.provider,
            model=response.model,
            finish_reason=response.finish_reason,
            usage=response.usage,
        )
