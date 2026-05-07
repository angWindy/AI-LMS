"""
Question bank models.
"""
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.assignment import QuestionDifficulty, QuestionPurposeType


if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.lesson import Lesson


class QuestionBankQuestion(Base, TimestampMixin):
    """Reusable question attached to a course and optionally one lesson."""

    __tablename__ = "question_bank_questions"

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
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    course: Mapped["Course"] = relationship("Course", back_populates="question_bank_questions")
    lesson: Mapped["Lesson | None"] = relationship("Lesson", back_populates="question_bank_questions")
    options: Mapped[List["QuestionBankOption"]] = relationship(
        "QuestionBankOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionBankOption.order_index",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<QuestionBankQuestion {self.id}>"


class QuestionBankOption(Base, TimestampMixin):
    """Multiple-choice option for a question bank question."""

    __tablename__ = "question_bank_options"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_bank_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    question: Mapped["QuestionBankQuestion"] = relationship("QuestionBankQuestion", back_populates="options")

    def __repr__(self) -> str:
        return f"<QuestionBankOption {self.id}>"
