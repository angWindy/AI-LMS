"""
Assignment schemas for API validation.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AssignmentOptionBase(BaseModel):
    """Option payload for a multiple-choice question."""

    option_text: str
    is_correct: bool = False


class AssignmentOptionCreate(AssignmentOptionBase):
    """Option creation schema."""


class AssignmentOptionResponse(AssignmentOptionBase):
    """Option response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    order_index: int
    created_at: datetime
    updated_at: datetime


class AssignmentQuestionBase(BaseModel):
    """Question payload schema."""

    question_text: str
    explanation: Optional[str] = None


class AssignmentQuestionCreate(AssignmentQuestionBase):
    """Question creation schema with exactly 4 choices."""

    options: List[AssignmentOptionCreate]

    @model_validator(mode="after")
    def validate_options(self):
        if len(self.options) != 4:
            raise ValueError("Each question must contain exactly 4 options")

        correct_count = sum(1 for option in self.options if option.is_correct)
        if correct_count != 1:
            raise ValueError("Each question must have exactly 1 correct option")

        return self


class AssignmentQuestionResponse(AssignmentQuestionBase):
    """Question response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assignment_id: uuid.UUID
    order_index: int
    options: List[AssignmentOptionResponse]
    created_at: datetime
    updated_at: datetime


class AssignmentBase(BaseModel):
    """Base assignment schema."""

    title: str


class AssignmentCreate(AssignmentBase):
    """Assignment creation schema."""

    lesson_id: Optional[uuid.UUID] = None
    questions: List[AssignmentQuestionCreate]

    @model_validator(mode="after")
    def validate_questions(self):
        if not self.questions:
            raise ValueError("Assignment must contain at least 1 question")
        return self


class AssignmentGenerateDraftRequest(BaseModel):
    """Payload for creating an AI-generated assignment draft."""

    lesson_id: uuid.UUID
    question_count: int = Field(..., ge=1, le=20)
    title: Optional[str] = None


class AssignmentUpdate(BaseModel):
    """Assignment update schema."""

    title: Optional[str] = None
    is_published: Optional[bool] = None
    questions: Optional[List[AssignmentQuestionCreate]] = None

    @model_validator(mode="after")
    def validate_questions(self):
        if self.questions is None:
            return self

        if not self.questions:
            raise ValueError("Assignment must contain at least 1 question")

        return self


class AssignmentResponse(AssignmentBase):
    """Assignment response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    lesson_id: Optional[uuid.UUID] = None
    is_published: bool
    order_index: int
    questions: List[AssignmentQuestionResponse]
    created_at: datetime
    updated_at: datetime
