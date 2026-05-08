"""Slide deck schemas for API validation."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SlideDeckGenerateDraftRequest(BaseModel):
    """Payload for creating an AI-generated slide deck draft."""

    lesson_id: uuid.UUID
    slide_count: int = Field(..., ge=1, le=50)
    title: str | None = None


class SlideDeckResponse(BaseModel):
    """Generated slide deck response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    lesson_id: uuid.UUID
    title: str
    slide_count: int
    ir_json: dict[str, Any]
    slides_json: dict[str, Any]
    pdf_url: str | None = None
    pdf_file_size: int | None = None
    pdf_mime_type: str | None = None
    provider: str | None = None
    model: str | None = None
    is_published: bool
    order_index: int
    created_at: datetime
    updated_at: datetime
