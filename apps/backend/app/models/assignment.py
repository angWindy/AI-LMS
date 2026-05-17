"""
Assignment models.
"""
import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.lesson import Lesson
    from app.models.submission import Submission


class QuestionDifficulty(str, enum.Enum):  # noqa: UP042
    """Question difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionPurposeType(str, enum.Enum):  # noqa: UP042
    """Question intended usage type."""

    PRACTICE = "practice"
    ASSESSMENT = "assessment"
    SHARED = "shared"


class AssignmentType(str, enum.Enum):  # noqa: UP042
    """Assignment workflow type."""

    PRACTICE = "practice"
    TEST = "test"


class AssignmentQuestionType(str, enum.Enum):  # noqa: UP042
    """Question answer mode inside an assignment."""

    MULTIPLE_CHOICE = "multiple_choice"
    ESSAY = "essay"


class Assignment(Base, TimestampMixin):
    """Assignment container that groups multiple choice questions."""

    __tablename__ = "assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    assignment_type: Mapped[AssignmentType] = mapped_column(
        Enum(AssignmentType),
        default=AssignmentType.PRACTICE,
        nullable=False,
        index=True,
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="assignments")
    lesson: Mapped["Lesson | None"] = relationship("Lesson", back_populates="assignments")
    questions: Mapped[list["AssignmentQuestion"]] = relationship(
        "AssignmentQuestion",
        back_populates="assignment",
        cascade="all, delete-orphan",
        order_by="AssignmentQuestion.order_index",
        lazy="selectin",
    )
    submissions: Mapped[list["Submission"]] = relationship(
        "Submission",
        back_populates="assignment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    lesson_scopes: Mapped[list["AssignmentLessonScope"]] = relationship(
        "AssignmentLessonScope",
        back_populates="assignment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Assignment {self.title}>"

    @property
    def scoped_lesson_ids(self) -> list[uuid.UUID]:
        """Lesson ids that define the question scope for course-level tests."""
        return [scope.lesson_id for scope in sorted(self.lesson_scopes, key=lambda item: item.order_index)]


class AssignmentQuestion(Base, TimestampMixin):
    """Question inside an assignment."""

    __tablename__ = "assignment_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[AssignmentQuestionType] = mapped_column(
        Enum(AssignmentQuestionType),
        default=AssignmentQuestionType.MULTIPLE_CHOICE,
        nullable=False,
        index=True,
    )
    correct_answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[QuestionDifficulty] = mapped_column(
        Enum(QuestionDifficulty),
        default=QuestionDifficulty.EASY,
        nullable=False,
        index=True,
    )
    purpose_type: Mapped[QuestionPurposeType] = mapped_column(
        Enum(QuestionPurposeType),
        default=QuestionPurposeType.SHARED,
        nullable=False,
        index=True,
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="questions")
    options: Mapped[list["AssignmentOption"]] = relationship(
        "AssignmentOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="AssignmentOption.order_index",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<AssignmentQuestion {self.id}>"


class AssignmentLessonScope(Base, TimestampMixin):
    """Lesson included in a course-level test question scope."""

    __tablename__ = "assignment_lesson_scopes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="lesson_scopes")
    lesson: Mapped["Lesson"] = relationship("Lesson")

    def __repr__(self) -> str:
        return f"<AssignmentLessonScope assignment={self.assignment_id} lesson={self.lesson_id}>"


class AssignmentOption(Base, TimestampMixin):
    """Multiple-choice option for a question."""

    __tablename__ = "assignment_options"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignment_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    question: Mapped["AssignmentQuestion"] = relationship("AssignmentQuestion", back_populates="options")

    def __repr__(self) -> str:
        return f"<AssignmentOption {self.id}>"
