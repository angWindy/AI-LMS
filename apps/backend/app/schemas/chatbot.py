"""Schemas for chatbot API requests and responses."""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessagePayload(BaseModel):
    """Client-provided chat message."""

    role: str = Field(..., examples=["system", "user", "assistant"])
    content: str = Field(..., min_length=0)


class ContextTracePayload(BaseModel):
    """Context data that informed the assistant response."""

    rag_context: list[str] = Field(default_factory=list)
    image_contexts: list[str] = Field(default_factory=list)
    conversation_history: list[str] = Field(default_factory=list)
    merged_context: str | None = None


class TeachingImagePayload(BaseModel):
    """Client-provided teaching screenshot to pass to multimodal LLM."""

    mime_type: Literal["image/png", "image/jpeg", "image/webp", "image/gif"]
    data_base64: str = Field(..., min_length=1)
    description: str | None = Field(default=None, max_length=500)
    source: str | None = Field(default="screen_capture", max_length=100)


class ConversationSummaryPayload(BaseModel):
    """Conversation metadata for listing conversations per learner."""

    id: uuid.UUID
    title: str | None = None
    course_id: uuid.UUID | None = None
    lesson_id: uuid.UUID | None = None
    is_active: bool
    updated_at: datetime


class ConversationMessagePayload(BaseModel):
    """Persisted message in a conversation thread."""

    id: uuid.UUID
    role: str
    content: str
    model_version: str | None = None
    tokens_used: int | None = None
    created_at: datetime


class ConversationMessagesResponse(BaseModel):
    """Message list for one conversation thread."""

    conversation_id: uuid.UUID
    messages: list[ConversationMessagePayload] = Field(default_factory=list)


class ChatbotAskRequest(BaseModel):
    """Ask request payload for chatbot endpoint."""

    question: str = Field(..., min_length=1)
    conversation_id: uuid.UUID | None = None
    conversation_title: str | None = Field(default=None, max_length=255)
    course_id: uuid.UUID | None = None
    lesson_id: uuid.UUID | None = None
    history: list[ChatMessagePayload] = Field(default_factory=list)
    context_docs: list[str] = Field(default_factory=list)
    image_contexts: list[str] = Field(default_factory=list)
    teaching_images: list[TeachingImagePayload] = Field(default_factory=list)
    system_prompt: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_output_tokens: int | None = Field(default=None, ge=1, le=8192)
    thinking_level: Literal["low", "medium", "high"] | None = None


class AssignmentChatbotAskRequest(BaseModel):
    """Ask request payload for assignment support chatbot endpoint."""

    question: str = Field(..., min_length=1)
    assignment_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    history: list[ChatMessagePayload] = Field(default_factory=list)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_output_tokens: int | None = Field(default=None, ge=1, le=8192)
    thinking_level: Literal["low", "medium", "high"] | None = None


class AssignmentChatbotPreloadRequest(BaseModel):
    """Request payload for warming assignment chatbot context."""

    assignment_id: uuid.UUID


class AssignmentChatbotPreloadResponse(BaseModel):
    """Response payload for assignment chatbot context preload."""

    assignment_id: uuid.UUID
    question_count: int
    context_length: int


class ChatbotAskResponse(BaseModel):
    """Chatbot response payload."""

    model_config = ConfigDict(from_attributes=True)

    answer: str
    conversation_id: uuid.UUID
    conversation_title: str | None = None
    provider: str
    model: str
    finish_reason: str | None = None
    usage: dict[str, int] | None = None
    messages: list[ChatMessagePayload] = Field(default_factory=list)
    context: ContextTracePayload | None = None
