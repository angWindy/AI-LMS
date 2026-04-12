"""
Assignment models.
"""
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Boolean, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base, TimestampMixin


if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.lesson import Lesson
    from app.models.submission import Submission


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
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="assignments")
    lesson: Mapped["Lesson | None"] = relationship("Lesson", back_populates="assignments")
    questions: Mapped[List["AssignmentQuestion"]] = relationship(
        "AssignmentQuestion",
        back_populates="assignment",
        cascade="all, delete-orphan",
        order_by="AssignmentQuestion.order_index",
        lazy="selectin",
    )
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission",
        back_populates="assignment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Assignment {self.title}>"


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
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="questions")
    options: Mapped[List["AssignmentOption"]] = relationship(
        "AssignmentOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="AssignmentOption.order_index",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<AssignmentQuestion {self.id}>"


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
