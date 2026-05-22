"""
Lesson model.
"""
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Boolean, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base, TimestampMixin


if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.material import Material
    from app.models.lesson_progress import LessonProgress
    from app.models.assignment import Assignment
    from app.models.question_bank import QuestionBankQuestion


class Lesson(Base, TimestampMixin):
    """Lesson model (belongs to a course)."""

    __tablename__ = "lessons"

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
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # Rich text content
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)  # in seconds
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_preview: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Free preview

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="lessons")
    materials: Mapped[List["Material"]] = relationship(
        "Material",
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="Material.order_index",
        lazy="selectin",
    )
    progress_records: Mapped[List["LessonProgress"]] = relationship(
        "LessonProgress",
        back_populates="lesson",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment",
        back_populates="lesson",
        lazy="selectin",
    )
    question_bank_questions: Mapped[List["QuestionBankQuestion"]] = relationship(
        "QuestionBankQuestion",
        back_populates="lesson",
        lazy="selectin",
    )
    def __repr__(self) -> str:
        return f"<Lesson {self.title}>"
