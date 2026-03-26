"""
Lesson schemas for API validation.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class LessonBase(BaseModel):
    """Base lesson schema."""
    title: str
    description: Optional[str] = None
    content: Optional[str] = None


class LessonCreate(LessonBase):
    """Lesson creation schema."""
    order_index: Optional[int] = None
    is_preview: bool = False


class LessonUpdate(BaseModel):
    """Lesson update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    is_preview: Optional[bool] = None
    is_published: Optional[bool] = None


class LessonOrderUpdate(BaseModel):
    """Lesson reorder schema."""
    order_index: int


class LessonResponse(LessonBase):
    """Lesson response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    video_url: Optional[str] = None
    video_duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    order_index: int
    is_published: bool
    is_preview: bool
    created_at: datetime
    updated_at: datetime


class LessonDetailResponse(LessonResponse):
    """Detailed lesson response with materials."""
    materials: List["MaterialResponse"] = []


class LessonProgressUpdate(BaseModel):
    """Update lesson progress."""
    watched_seconds: int
    last_position: int
    is_completed: bool = False


class LessonProgressResponse(BaseModel):
    """Lesson progress response."""
    model_config = ConfigDict(from_attributes=True)

    lesson_id: uuid.UUID
    watched_seconds: int
    total_seconds: Optional[int] = None
    is_completed: bool
    last_position: int
    last_accessed_at: datetime


# Material schemas (related to lesson)
class MaterialBase(BaseModel):
    """Base material schema."""
    title: str
    description: Optional[str] = None
    type: str


class MaterialCreate(MaterialBase):
    """Material creation schema."""
    order_index: Optional[int] = None


class MaterialResponse(MaterialBase):
    """Material response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lesson_id: uuid.UUID
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    order_index: int
    created_at: datetime


# Update forward references
LessonDetailResponse.model_rebuild()
