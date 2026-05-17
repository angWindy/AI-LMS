"""Workflow for generating assignment submission feedback with an LLM."""
from dataclasses import dataclass

from llm.config import LLMConfig
from llm.models import ChatMessage, LLMRequest
from llm.prompts.assignment_feedback import build_assignment_feedback_prompt
from llm.providers.base import LLMProvider
from llm.providers.factory import get_llm_provider


@dataclass
class AssignmentFeedbackResult:
    """Raw LLM feedback result."""

    text: str
    provider: str
    model: str
    finish_reason: str | None
    usage: dict[str, int] | None


class AssignmentFeedbackWorkflow:
    """Run post-submission feedback prompts against the configured provider."""

    def __init__(
        self,
        config: LLMConfig,
        provider: LLMProvider | None = None,
    ) -> None:
        self.config = config
        self.provider = provider or get_llm_provider(config)

    def run(
        self,
        course_context: str,
        scope_context: str,
        submission_context: str,
    ) -> AssignmentFeedbackResult:
        """Generate submission feedback in JSON text format."""
        system_prompt = build_assignment_feedback_prompt(
            course_context=course_context,
            scope_context=scope_context,
            submission_context=submission_context,
        )

        metadata = {"request_timeout_seconds": 1800}
        if self.provider.supports_json_mode:
            metadata["response_mime_type"] = "application/json"

        response = self.provider.generate(
            LLMRequest(
                messages=[
                    ChatMessage(
                        role="user",
                        content="Evaluate the submitted assignment and return the required JSON.",
                    )
                ],
                system_prompt=system_prompt,
                temperature=0.1,
                max_output_tokens=None,
                thinking_level=self.config.thinking_level,
                metadata=metadata,
            )
        )

        return AssignmentFeedbackResult(
            text=response.text,
            provider=response.provider,
            model=response.model,
            finish_reason=response.finish_reason,
            usage=response.usage,
        )
