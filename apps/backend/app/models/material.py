"""
Material model (additional resources for lessons).
"""
import enum
import uuid

from sqlalchemy import String, Text, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base, TimestampMixin


class MaterialType(str, enum.Enum):
    """Type of learning material."""
    VIDEO = "video"
    DOCUMENT = "document"
    LINK = "link"
    QUIZ = "quiz"


class Material(Base, TimestampMixin):
    """Additional material for a lesson."""

    __tablename__ = "materials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
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
    lesson = relationship("Lesson", back_populates="materials")

    def __repr__(self) -> str:
        return f"<Material {self.title}>"
