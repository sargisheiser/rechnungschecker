"""User and guest usage models."""

import enum
from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Enum, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PlanType(str, enum.Enum):
    """Subscription plan types."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    STEUERBERATER = "steuerberater"


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Email verification
    verification_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    verification_code_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Subscription
    plan: Mapped[PlanType] = mapped_column(
        Enum(PlanType, values_callable=lambda x: [e.value for e in x]),
        default=PlanType.FREE
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan_valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Usage tracking (reset monthly)
    validations_this_month: Mapped[int] = mapped_column(Integer, default=0)
    conversions_this_month: Mapped[int] = mapped_column(Integer, default=0)
    usage_reset_date: Mapped[date] = mapped_column(Date, default=date.today)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def get_validation_limit(self) -> int | None:
        """Return monthly validation limit based on plan. None = unlimited."""
        limits = {
            PlanType.FREE: 5,
            PlanType.STARTER: 100,
            PlanType.PRO: None,  # Unlimited
            PlanType.STEUERBERATER: None,  # Unlimited
        }
        return limits[self.plan]

    def get_conversion_limit(self) -> int:
        """Return monthly conversion limit based on plan."""
        limits = {
            PlanType.FREE: 0,
            PlanType.STARTER: 20,
            PlanType.PRO: 100,
            PlanType.STEUERBERATER: 500,
        }
        return limits[self.plan]

    def can_validate(self) -> bool:
        """Check if user can perform another validation."""
        limit = self.get_validation_limit()
        if limit is None:
            return True
        return self.validations_this_month < limit

    def can_convert(self) -> bool:
        """Check if user can perform another conversion."""
        limit = self.get_conversion_limit()
        return self.conversions_this_month < limit

    def can_use_api(self) -> bool:
        """Check if user's plan allows API access."""
        return self.plan in (PlanType.PRO, PlanType.STEUERBERATER)

    def get_api_calls_limit(self) -> int:
        """Return monthly API call limit based on plan."""
        limits = {
            PlanType.FREE: 0,
            PlanType.STARTER: 0,
            PlanType.PRO: 1000,
            PlanType.STEUERBERATER: 5000,
        }
        return limits[self.plan]

    def get_max_api_keys(self) -> int:
        """Return maximum number of API keys allowed based on plan."""
        limits = {
            PlanType.FREE: 0,
            PlanType.STARTER: 0,
            PlanType.PRO: 5,
            PlanType.STEUERBERATER: 20,
        }
        return limits[self.plan]

    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="user", cascade="all, delete-orphan")
    webhooks = relationship("WebhookSubscription", back_populates="user", cascade="all, delete-orphan")

    def can_manage_clients(self) -> bool:
        """Check if user's plan allows client management."""
        return self.plan == PlanType.STEUERBERATER

    def get_max_clients(self) -> int:
        """Return maximum number of clients allowed based on plan."""
        limits = {
            PlanType.FREE: 0,
            PlanType.STARTER: 0,
            PlanType.PRO: 0,
            PlanType.STEUERBERATER: 100,
        }
        return limits[self.plan]

    def can_use_webhooks(self) -> bool:
        """Check if user's plan allows webhook access."""
        return self.plan in (PlanType.PRO, PlanType.STEUERBERATER)

    def get_max_webhooks(self) -> int:
        """Return maximum number of webhooks allowed based on plan."""
        limits = {
            PlanType.FREE: 0,
            PlanType.STARTER: 0,
            PlanType.PRO: 5,
            PlanType.STEUERBERATER: 20,
        }
        return limits[self.plan]


class EmailVerificationToken(Base):
    """Email verification tokens for new users."""

    __tablename__ = "email_verification_tokens"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), index=True
    )
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.is_expired() and self.used_at is None


class GuestUsage(Base):
    """Track validation usage for non-registered users."""

    __tablename__ = "guest_usage"
    __table_args__ = (
        Index("ix_guest_usage_ip_cookie", "ip_address", "cookie_id"),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    ip_address: Mapped[str] = mapped_column(String(45), index=True)  # IPv6 max length
    cookie_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    validations_used: Mapped[int] = mapped_column(Integer, default=0)
    first_validation_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    last_validation_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def can_validate(self, limit: int = 5) -> bool:
        """Check if guest can perform another validation."""
        return self.validations_used < limit
