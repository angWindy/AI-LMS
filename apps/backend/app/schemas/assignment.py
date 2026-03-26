"""
Assignment schemas for API validation.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class AssignmentBase(BaseModel):
    """Base assignment schema."""
    title: str
    description: str
    instructions: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    """Assignment creation schema."""
    lesson_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    max_score: float = 100.0
    allow_late_submission: bool = False
    late_penalty_percent: float = 0.0


class AssignmentUpdate(BaseModel):
    """Assignment update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None
    max_score: Optional[float] = None
    allow_late_submission: Optional[bool] = None
    late_penalty_percent: Optional[float] = None
    is_published: Optional[bool] = None


class AssignmentResponse(AssignmentBase):
    """Assignment response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    lesson_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    max_score: float
    allow_late_submission: bool
    late_penalty_percent: float
    is_published: bool
    order_index: int
    created_at: datetime
    updated_at: datetime


# Submission schemas
class SubmissionCreate(BaseModel):
    """Submission creation schema."""
    content: Optional[str] = None


class SubmissionUpdate(BaseModel):
    """Submission update schema (before grading)."""
    content: Optional[str] = None


class SubmissionGrade(BaseModel):
    """Grade submission schema."""
    score: float
    feedback: Optional[str] = None


class SubmissionResponse(BaseModel):
    """Submission response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assignment_id: uuid.UUID
    user_id: uuid.UUID
    content: Optional[str] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    status: str
    score: Optional[float] = None
    feedback: Optional[str] = None
    submitted_at: datetime
    graded_at: Optional[datetime] = None
    is_late: bool


class SubmissionDetailResponse(SubmissionResponse):
    """Detailed submission with user info."""
    user_name: str
    user_email: str
