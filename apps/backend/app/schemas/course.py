"""
Course schemas for API validation.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.course import CourseLevel, CourseStatus
from app.schemas.user import UserResponse


class CourseBase(BaseModel):
    """Base course schema."""
    title: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    level: CourseLevel
    language: str = "vi"


class CourseCreate(CourseBase):
    """Course creation schema."""
    pass


class CourseUpdate(BaseModel):
    """Course update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    level: CourseLevel | None = None
    language: Optional[str] = None
    thumbnail_url: Optional[str] = None


class CourseResponse(CourseBase):
    """Course response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    instructor_id: uuid.UUID
    thumbnail_url: Optional[str] = None
    status: CourseStatus
    estimated_duration: Optional[int] = None
    is_featured: bool
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None


class CourseDetailResponse(CourseResponse):
    """Detailed course response with instructor info."""
    instructor: UserResponse
    lesson_count: int = 0


class CourseListResponse(BaseModel):
    """Course list item response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    short_description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: CourseStatus
    level: CourseLevel
    instructor: UserResponse
    lesson_count: int = 0
