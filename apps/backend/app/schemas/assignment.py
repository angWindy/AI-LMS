"""
Assignment schemas for API validation.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.assignment import (
    AssignmentQuestionType,
    AssignmentType,
    QuestionDifficulty,
    QuestionPurposeType,
)
from app.models.submission import SubmissionStatus


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
    question_type: AssignmentQuestionType = AssignmentQuestionType.MULTIPLE_CHOICE
    correct_answer_text: str | None = None
    difficulty: QuestionDifficulty = QuestionDifficulty.EASY
    purpose_type: QuestionPurposeType = QuestionPurposeType.SHARED


class AssignmentQuestionCreate(AssignmentQuestionBase):
    """Question creation schema."""

    options: list[AssignmentOptionCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_options(self):
        if self.question_type == AssignmentQuestionType.ESSAY:
            if not (self.correct_answer_text or "").strip():
                raise ValueError("Essay questions must include correct_answer_text")
            return self

        if len(self.options) != 4:
            raise ValueError("Each multiple-choice question must contain exactly 4 options")

        correct_count = sum(1 for option in self.options if option.is_correct)
        if correct_count != 1:
            raise ValueError("Each multiple-choice question must have exactly 1 correct option")

        return self


class AssignmentQuestionResponse(AssignmentQuestionBase):
    """Question response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assignment_id: uuid.UUID
    order_index: int
    options: list[AssignmentOptionResponse]
    created_at: datetime
    updated_at: datetime


class AssignmentBase(BaseModel):
    """Base assignment schema."""

    title: str


class AssignmentCreate(AssignmentBase):
    """Assignment creation schema."""

    lesson_id: uuid.UUID | None = None
    assignment_type: AssignmentType = AssignmentType.PRACTICE
    questions: list[AssignmentQuestionCreate]

    @model_validator(mode="after")
    def validate_questions(self):
        if not self.questions:
            raise ValueError("Assignment must contain at least 1 question")
        return self


class AssignmentGenerateDraftRequest(BaseModel):
    """Payload for creating an AI-generated assignment draft."""

    lesson_id: uuid.UUID
    question_count: int = Field(..., ge=1, le=20)
    title: str | None = None


class AssignmentGenerateFromBankRequest(BaseModel):
    """Payload for creating a review assignment from reusable question bank items."""

    lesson_id: uuid.UUID | None = None
    question_count: int = Field(..., ge=1, le=100)
    title: str | None = None


class AssignmentGenerateTestRequest(BaseModel):
    """Payload for creating a course-level test from reusable question bank items."""

    lesson_ids: list[uuid.UUID] = Field(default_factory=list)
    question_count: int = Field(..., ge=1, le=100)
    title: str | None = None


class AssignmentUpdate(BaseModel):
    """Assignment update schema."""

    title: str | None = None
    is_published: bool | None = None
    questions: list[AssignmentQuestionCreate] | None = None

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
    lesson_id: uuid.UUID | None = None
    assignment_type: AssignmentType
    scoped_lesson_ids: list[uuid.UUID] = Field(default_factory=list)
    is_published: bool
    order_index: int
    questions: list[AssignmentQuestionResponse]
    created_at: datetime
    updated_at: datetime


class AssignmentSubmitAnswer(BaseModel):
    """Learner answer for one question."""

    question_id: uuid.UUID
    selected_option_id: uuid.UUID | None = None
    answer_text: str | None = None


class AssignmentSubmitRequest(BaseModel):
    """Learner assignment submission payload."""

    answers: list[AssignmentSubmitAnswer]


class SubmissionAnswerResponse(BaseModel):
    """Saved per-question result."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    submission_id: uuid.UUID
    question_id: uuid.UUID
    selected_option_id: uuid.UUID | None = None
    answer_text: str | None = None
    is_correct: bool | None = None
    score: float | None = None
    explanation: str | None = None
    feedback: str | None = None
    correct_answer_text: str | None = None


class SubmissionResponse(BaseModel):
    """Submission result with saved answers and AI feedback."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assignment_id: uuid.UUID
    user_id: uuid.UUID
    status: SubmissionStatus
    score: float | None = None
    feedback: str | None = None
    submitted_at: datetime
    graded_at: datetime | None = None
    is_late: bool
    answers: list[SubmissionAnswerResponse]
