"""Generated lecture slide deck model."""
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.lesson import Lesson


class SlideDeck(Base, TimestampMixin):
    """AI-generated lecture slides attached to a lesson."""

    __tablename__ = "slide_decks"

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
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slide_count: Mapped[int] = mapped_column(Integer, nullable=False)
    ir_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    slides_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pdf_mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="slide_decks")
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="slide_decks")

    def __repr__(self) -> str:
        return f"<SlideDeck {self.title}>"
