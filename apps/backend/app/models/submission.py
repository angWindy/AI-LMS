"""
Submission model.
"""
import enum
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.assignment import Assignment, AssignmentOption, AssignmentQuestion
    from app.models.user import User


class SubmissionStatus(str, enum.Enum):  # noqa: UP042
    """Submission status."""
    SUBMITTED = "submitted"
    GRADED = "graded"
    RETURNED = "returned"


class Submission(Base):
    """Student submission for an assignment."""

    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("assignment_id", "user_id", name="uq_assignment_user"),
    )

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
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # Text submission
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus),
        default=SubmissionStatus.SUBMITTED,
        nullable=False,
        index=True,
    )
    score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )
    graded_at: Mapped[datetime | None] = mapped_column(nullable=True)
    graded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    is_late: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="submissions")
    answers: Mapped[list["SubmissionAnswer"]] = relationship(
        "SubmissionAnswer",
        back_populates="submission",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="submissions",
        foreign_keys=[user_id],
    )
    grader = relationship("User", foreign_keys=[graded_by])

    def __repr__(self) -> str:
        return f"<Submission assignment={self.assignment_id} user={self.user_id}>"


class SubmissionAnswer(Base):
    """Saved answer and AI feedback for one assignment question."""

    __tablename__ = "submission_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignment_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    selected_option_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignment_options.id", ondelete="SET NULL"),
        nullable=True,
    )
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="answers")
    question: Mapped["AssignmentQuestion"] = relationship("AssignmentQuestion")
    selected_option: Mapped["AssignmentOption | None"] = relationship("AssignmentOption")

    def __repr__(self) -> str:
        return f"<SubmissionAnswer submission={self.submission_id} question={self.question_id}>"
