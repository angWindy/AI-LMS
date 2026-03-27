"""
Refresh token model for JWT refresh token storage.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


def _default_expiry():
    """Default expiry time for refresh tokens (7 days)."""
    from app.core.config import settings
    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


class RefreshToken(Base):
    """Stored refresh tokens for JWT authentication."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(default=_default_expiry, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<RefreshToken {self.id}>"
