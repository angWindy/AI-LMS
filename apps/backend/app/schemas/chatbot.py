"""Schemas for chatbot API requests and responses."""
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class ChatMessagePayload(BaseModel):
    """Client-provided chat message."""

    role: str = Field(..., examples=["system", "user", "assistant"])
    content: str = Field(..., min_length=0)


class ContextTracePayload(BaseModel):
    """Context data that informed the assistant response."""

    rag_context: list[str] = Field(default_factory=list)
    image_contexts: list[str] = Field(default_factory=list)
    merged_context: str | None = None


class ChatbotAskRequest(BaseModel):
    """Ask request payload for chatbot endpoint."""

    question: str = Field(..., min_length=1)
    history: list[ChatMessagePayload] = Field(default_factory=list)
    context_docs: list[str] = Field(default_factory=list)
    image_contexts: list[str] = Field(default_factory=list)
    system_prompt: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_output_tokens: int | None = Field(default=None, ge=1, le=8192)
    thinking_level: Literal["low", "medium", "high"] | None = None


class ChatbotAskResponse(BaseModel):
    """Chatbot response payload."""

    model_config = ConfigDict(from_attributes=True)

    answer: str
    provider: str
    model: str
    finish_reason: str | None = None
    usage: dict[str, int] | None = None
    messages: list[ChatMessagePayload] = Field(default_factory=list)
    context: ContextTracePayload | None = None