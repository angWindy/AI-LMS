"""
Question bank schemas for API validation.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.assignment import QuestionDifficulty, QuestionPurposeType


class QuestionBankCourseResponse(BaseModel):
    """Course option visible in the question bank."""

    id: uuid.UUID
    title: str
    slug: str
    instructor_id: uuid.UUID


class QuestionBankOptionBase(BaseModel):
    """Option payload for a reusable multiple-choice question."""

    option_text: str
    is_correct: bool = False


class QuestionBankOptionCreate(QuestionBankOptionBase):
    """Option creation schema."""


class QuestionBankOptionResponse(QuestionBankOptionBase):
    """Option response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    order_index: int
    created_at: datetime
    updated_at: datetime


class QuestionBankQuestionBase(BaseModel):
    """Question bank payload schema."""

    question_text: str
    explanation: Optional[str] = None
    difficulty: QuestionDifficulty = QuestionDifficulty.EASY
    purpose_type: QuestionPurposeType = QuestionPurposeType.SHARED


class QuestionBankQuestionCreate(QuestionBankQuestionBase):
    """Create a reusable question for a course."""

    course_id: uuid.UUID
    lesson_id: Optional[uuid.UUID] = None
    options: List[QuestionBankOptionCreate]

    @model_validator(mode="after")
    def validate_options(self):
        if len(self.options) != 4:
            raise ValueError("Each question must contain exactly 4 options")

        correct_count = sum(1 for option in self.options if option.is_correct)
        if correct_count != 1:
            raise ValueError("Each question must have exactly 1 correct option")

        return self


class QuestionBankQuestionUpdate(QuestionBankQuestionBase):
    """Update details for an existing reusable question."""

    lesson_id: Optional[uuid.UUID] = None
    options: Optional[List[QuestionBankOptionCreate]] = None

    @model_validator(mode="after")
    def validate_options(self):
        if self.options is None:
            return self

        if len(self.options) != 4:
            raise ValueError("Each question must contain exactly 4 options")

        correct_count = sum(1 for option in self.options if option.is_correct)
        if correct_count != 1:
            raise ValueError("Each question must have exactly 1 correct option")

        return self


class QuestionBankQuestionResponse(QuestionBankQuestionBase):
    """Question bank response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    lesson_id: Optional[uuid.UUID] = None
    order_index: int
    course_title: str
    lesson_title: Optional[str] = None
    options: List[QuestionBankOptionResponse]
    created_at: datetime
    updated_at: datetime


class QuestionBankGenerateRequest(BaseModel):
    """Payload for generating reusable questions for the question bank."""

    course_id: uuid.UUID
    lesson_id: uuid.UUID
    question_count: int = Field(..., ge=1, le=20)
    difficulty: QuestionDifficulty = QuestionDifficulty.EASY
    purpose_type: QuestionPurposeType = QuestionPurposeType.SHARED
