"""Shared models for provider-agnostic LLM interactions."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatMessage:
    """Single chat message exchanged with an LLM."""

    role: str
    content: str


@dataclass
class LLMRequest:
    """Normalized request structure sent to an LLM provider."""

    messages: list[ChatMessage]
    system_prompt: str | None = None
    temperature: float = 1.0
    max_output_tokens: int = 512
    thinking_level: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Normalized response structure returned by an LLM provider."""

    text: str
    provider: str
    model: str
    finish_reason: str | None = None
    usage: dict[str, int] | None = None
    raw: dict[str, Any] | None = None


@dataclass
class ContextTrace:
    """Trace data that informed the LLM response."""

    rag_context: list[str] = field(default_factory=list)
    image_contexts: list[str] = field(default_factory=list)
    merged_context: str | None = None
