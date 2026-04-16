"""Chatbot workflow that stitches prompts, context, and LLM calls."""
from dataclasses import dataclass
from collections.abc import Sequence

from llm.config import LLMConfig
from llm.models import ChatMessage, ContextTrace, ImageInput, LLMRequest
from llm.prompts.chatbot import default_chatbot_prompt
from llm.providers.base import LLMProvider
from llm.providers.factory import get_llm_provider
from llm.rag.context_builder import ContextBuilder, DefaultContextBuilder


@dataclass
class ChatbotResult:
    """Result payload for chatbot generation."""

    answer: str
    provider: str
    model: str
    finish_reason: str | None
    usage: dict[str, int] | None
    messages: list[ChatMessage]
    context: ContextTrace


class ChatbotWorkflow:
    """Workflow for running chat interactions with optional context."""

    def __init__(
        self,
        config: LLMConfig,
        provider: LLMProvider | None = None,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self.config = config
        self.provider = provider or get_llm_provider(config)
        self.context_builder = context_builder or DefaultContextBuilder()

    def run(
        self,
        question: str,
        history: Sequence[ChatMessage] | None = None,
        system_prompt: str | None = None,
        rag_context: Sequence[str] | None = None,
        image_contexts: Sequence[str] | None = None,
        images: Sequence[ImageInput] | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        thinking_level: str | None = None,
    ) -> ChatbotResult:
        """Generate an assistant response with context trace."""
        incoming_history = list(history or [])
        history_system_prompt = _merge_system_messages(incoming_history)
        chat_history = [m for m in incoming_history if m.role != "system"]
        chat_history.append(ChatMessage(role="user", content=question))

        context_trace = self.context_builder.build_context(
            question=question,
            rag_context=rag_context,
            image_contexts=image_contexts,
        )

        base_system_prompt = system_prompt or default_chatbot_prompt()
        merged_system_prompt = _merge_system_prompts(
            _merge_system_prompts(base_system_prompt, history_system_prompt),
            context_trace.merged_context,
        )

        request = LLMRequest(
            messages=chat_history,
            system_prompt=merged_system_prompt,
            temperature=self.config.temperature if temperature is None else temperature,
            max_output_tokens=(
                self.config.max_output_tokens
                if max_output_tokens is None
                else max_output_tokens
            ),
            thinking_level=(
                self.config.thinking_level
                if thinking_level is None
                else thinking_level
            ),
            images=list(images or []),
        )

        response = self.provider.generate(request)

        trace_messages = [
            ChatMessage(role="system", content=context_trace.merged_context or ""),
            ChatMessage(role="user", content=question),
            ChatMessage(role="assistant", content=response.text),
        ]

        return ChatbotResult(
            answer=response.text,
            provider=response.provider,
            model=response.model,
            finish_reason=response.finish_reason,
            usage=response.usage,
            messages=trace_messages,
            context=context_trace,
        )


def _merge_system_prompts(
    system_prompt: str | None,
    context: str | None,
) -> str | None:
    parts = [part.strip() for part in [system_prompt, context] if part]
    if not parts:
        return None
    return "\n\n".join(parts)


def _merge_system_messages(messages: Sequence[ChatMessage]) -> str | None:
    system_parts = [
        message.content.strip()
        for message in messages
        if message.role == "system" and message.content.strip()
    ]
    if not system_parts:
        return None
    return "\n\n".join(system_parts)
