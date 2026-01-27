"""API Key model for programmatic access."""

import secrets
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def generate_api_key() -> str:
    """Generate a secure API key with prefix for identification."""
    # Format: rc_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx (32 random chars)
    return f"rc_live_{secrets.token_hex(16)}"


def generate_key_hash(key: str) -> str:
    """Hash the API key for secure storage."""
    import hashlib
    return hashlib.sha256(key.encode()).hexdigest()


class APIKey(Base):
    """API Key for programmatic access."""

    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # Key identification (prefix shown to user, hash for lookup)
    key_prefix: Mapped[str] = mapped_column(String(16))  # e.g., "rc_live_a1b2"
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # Metadata
    name: Mapped[str] = mapped_column(String(100))  # User-defined name
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Usage tracking
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    # Rate limiting (per key)
    requests_this_month: Mapped[int] = mapped_column(Integer, default=0)
    requests_reset_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationship
    user = relationship("User", back_populates="api_keys")

    def is_expired(self) -> bool:
        """Check if API key has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC).replace(tzinfo=None) > self.expires_at

    def is_valid(self) -> bool:
        """Check if API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired()

    def record_usage(self) -> None:
        """Record API key usage."""
        self.last_used_at = datetime.now(UTC).replace(tzinfo=None)
        self.usage_count += 1
        self.requests_this_month += 1

    @classmethod
    def create_key(cls, user_id: UUID, name: str, description: str | None = None, expires_at: datetime | None = None) -> tuple["APIKey", str]:
        """Create a new API key and return the model and the raw key.

        The raw key is only available at creation time.
        """
        raw_key = generate_api_key()
        key_hash = generate_key_hash(raw_key)
        key_prefix = raw_key[:12] + "..."  # Show first 12 chars

        api_key = cls(
            user_id=user_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            name=name,
            description=description,
            expires_at=expires_at,
        )

        return api_key, raw_key
