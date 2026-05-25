"""
User model.
"""
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Boolean, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base, TimestampMixin


if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.submission import Submission


class UserRole(str, enum.Enum):
    """User roles in the system."""
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    LEARNER = "learner"


class User(Base, TimestampMixin):
    """User model."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.LEARNER,
        nullable=False,
        index=True,
    )
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    courses: Mapped[List["Course"]] = relationship(
        "Course",
        back_populates="instructor",
        lazy="selectin",
    )
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission",
        back_populates="user",
        foreign_keys="Submission.user_id",
        lazy="selectin",
    )

    def set_password(self, password: str) -> None:
        # Băm mật khẩu trước khi lưu.
        """Hash and set the password."""
        from app.core.security import get_password_hash
        self.password_hash = get_password_hash(password)

    def verify_password(self, password: str) -> bool:
        # Kiểm tra mật khẩu người dùng.
        """Verify the password against the stored hash."""
        from app.core.security import verify_password
        return verify_password(password, self.password_hash)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
