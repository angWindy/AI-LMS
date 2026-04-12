"""
Material model (additional resources for courses and lessons).
"""
import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Integer, ForeignKey, Enum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base, TimestampMixin


if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.lesson import Lesson


class MaterialType(str, enum.Enum):
    """Type of learning material."""
    VIDEO = "video"
    DOCUMENT = "document"
    LINK = "link"
    QUIZ = "quiz"


class Material(Base, TimestampMixin):
    """Additional material for a course or a lesson."""

    __tablename__ = "materials"
    __table_args__ = (
        CheckConstraint(
            "(course_id IS NOT NULL OR lesson_id IS NOT NULL)",
            name="ck_material_course_or_lesson",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[MaterialType] = mapped_column(Enum(MaterialType), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)  # in bytes
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    course: Mapped["Course | None"] = relationship("Course", back_populates="materials")
    lesson: Mapped["Lesson | None"] = relationship("Lesson", back_populates="materials")

    def __repr__(self) -> str:
        return f"<Material {self.title}>"
