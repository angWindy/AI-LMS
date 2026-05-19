"""Workflow for generating lecture slides with an LLM."""
from dataclasses import dataclass

from llm.config import LLMConfig
from llm.models import ChatMessage, LLMRequest
from llm.prompts.slide_generator import (
    build_document_to_ir_prompt,
    build_ir_to_slides_prompt,
)
from llm.providers.base import LLMProvider
from llm.providers.factory import get_llm_provider


@dataclass
class SlideGeneratorResult:
    """Raw LLM result for slide generation steps."""

    text: str
    provider: str
    model: str
    finish_reason: str | None
    usage: dict[str, int] | None


class SlideGeneratorWorkflow:
    """Run slide generation prompts against the configured provider."""

    def __init__(
        self,
        config: LLMConfig,
        provider: LLMProvider | None = None,
    ) -> None:
        self.config = config
        self.provider = provider or get_llm_provider(config)

    def generate_document_ir(
        self,
        course_context: str,
        lesson_context: str,
        course_level: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        thinking_level: str | None = None,
    ) -> SlideGeneratorResult:
        """Generate document IR JSON text from course and lesson context."""
        system_prompt = build_document_to_ir_prompt(
            course_context=course_context,
            lesson_context=lesson_context,
            course_level=course_level,
        )
        return self._run_json_prompt(
            system_prompt=system_prompt,
            user_message="Generate the document IR JSON now with the required format.",
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            thinking_level=thinking_level,
        )

    def generate_slides_from_ir(
        self,
        ir_json: str,
        slide_count: int,
        course_level: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        thinking_level: str | None = None,
    ) -> SlideGeneratorResult:
        """Generate slides JSON text from document IR JSON."""
        system_prompt = build_ir_to_slides_prompt(
            ir_json=ir_json,
            slide_count=slide_count,
            course_level=course_level,
        )
        return self._run_json_prompt(
            system_prompt=system_prompt,
            user_message="Generate the slides JSON now with the required format.",
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            thinking_level=thinking_level,
        )

    def generate_slides_from_context(
        self,
        course_context: str,
        lesson_context: str,
        slide_count: int,
        course_level: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        thinking_level: str | None = None,
    ) -> SlideGeneratorResult:
        """Generate slides JSON through the required context -> IR -> slides flow."""
        ir_result = self.generate_document_ir(
            course_context=course_context,
            lesson_context=lesson_context,
            course_level=course_level,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            thinking_level=thinking_level,
        )
        return self.generate_slides_from_ir(
            ir_json=ir_result.text,
            slide_count=slide_count,
            course_level=course_level,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            thinking_level=thinking_level,
        )

    def _run_json_prompt(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        thinking_level: str | None = None,
    ) -> SlideGeneratorResult:
        # Disable output token caps for generation unless explicitly overridden.
        token_budget = None if max_output_tokens is None else max_output_tokens

        metadata = {"request_timeout_seconds": 1800}
        if self.provider.supports_json_mode:
            metadata["response_mime_type"] = "application/json"

        request = LLMRequest(
            messages=[
                ChatMessage(
                    role="user",
                    content=user_message,
                )
            ],
            system_prompt=system_prompt,
            temperature=self.config.temperature if temperature is None else temperature,
            max_output_tokens=token_budget,
            thinking_level=(
                self.config.thinking_level if thinking_level is None else thinking_level
            ),
            metadata=metadata,
        )

        response = self.provider.generate(request)

        return SlideGeneratorResult(
            text=response.text,
            provider=response.provider,
            model=response.model,
            finish_reason=response.finish_reason,
            usage=response.usage,
        )


def generate_document_ir(
    course_context: str,
    lesson_context: str,
    config: LLMConfig | None = None,
    provider: LLMProvider | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
    thinking_level: str | None = None,
) -> SlideGeneratorResult:
    """Generate document IR JSON using a one-off workflow instance."""
    workflow = SlideGeneratorWorkflow(
        config=config or LLMConfig.from_env(),
        provider=provider,
    )
    return workflow.generate_document_ir(
        course_context=course_context,
        lesson_context=lesson_context,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        thinking_level=thinking_level,
    )


def generate_slides_from_ir(
    ir_json: str,
    slide_count: int,
    config: LLMConfig | None = None,
    provider: LLMProvider | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
    thinking_level: str | None = None,
) -> SlideGeneratorResult:
    """Generate slides JSON from document IR using a one-off workflow instance."""
    workflow = SlideGeneratorWorkflow(
        config=config or LLMConfig.from_env(),
        provider=provider,
    )
    return workflow.generate_slides_from_ir(
        ir_json=ir_json,
        slide_count=slide_count,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        thinking_level=thinking_level,
    )


def generate_slides_from_context(
    course_context: str,
    lesson_context: str,
    slide_count: int,
    config: LLMConfig | None = None,
    provider: LLMProvider | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
    thinking_level: str | None = None,
) -> SlideGeneratorResult:
    """Generate slides JSON through the required context -> IR -> slides flow."""
    workflow = SlideGeneratorWorkflow(
        config=config or LLMConfig.from_env(),
        provider=provider,
    )
    return workflow.generate_slides_from_context(
        course_context=course_context,
        lesson_context=lesson_context,
        slide_count=slide_count,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        thinking_level=thinking_level,
    )
