"""
Course model.
"""
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.lesson import Lesson
    from app.models.material import Material
    from app.models.assignment import Assignment
    from app.models.question_bank import QuestionBankQuestion
    from app.models.slide_deck import SlideDeck


class CourseStatus(str, enum.Enum):
    """Course publication status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CourseLevel(str, enum.Enum):
    """Academic level targeted by a course."""
    ELEMENTARY = "elementary"
    MIDDLE_SCHOOL = "middle_school"
    HIGH_SCHOOL = "high_school"
    HIGHER_EDUCATION = "higher_education"


class Course(Base, TimestampMixin):
    """Course model."""

    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint(
            "level IN ('elementary', 'middle_school', 'high_school', 'higher_education')",
            name="ck_courses_level_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    instructor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[CourseStatus] = mapped_column(
        Enum(CourseStatus),
        default=CourseStatus.DRAFT,
        nullable=False,
        index=True,
    )
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    level: Mapped[str] = mapped_column(
        String(50),
        default=CourseLevel.HIGHER_EDUCATION.value,
        server_default=CourseLevel.HIGHER_EDUCATION.value,
        nullable=False,
    )
    language: Mapped[str] = mapped_column(String(10), default="vi", nullable=False)
    estimated_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)  # in minutes
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    instructor: Mapped["User"] = relationship("User", back_populates="courses")
    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Lesson.order_index",
        lazy="selectin",
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment",
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    materials: Mapped[List["Material"]] = relationship(
        "Material",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Material.order_index",
        lazy="selectin",
    )
    question_bank_questions: Mapped[List["QuestionBankQuestion"]] = relationship(
        "QuestionBankQuestion",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="QuestionBankQuestion.order_index",
        lazy="selectin",
    )
    slide_decks: Mapped[List["SlideDeck"]] = relationship(
        "SlideDeck",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="SlideDeck.order_index",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Course {self.title}>"
