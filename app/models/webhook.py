"""Webhook subscription and delivery models."""

import enum
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WebhookEventType(str, enum.Enum):
    """Webhook event types."""

    VALIDATION_COMPLETED = "validation.completed"
    VALIDATION_VALID = "validation.valid"
    VALIDATION_INVALID = "validation.invalid"
    VALIDATION_WARNING = "validation.warning"


class DeliveryStatus(str, enum.Enum):
    """Webhook delivery status."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


def generate_webhook_secret() -> str:
    """Generate a secure webhook secret for HMAC signing."""
    return f"whsec_{secrets.token_hex(32)}"


class WebhookSubscription(Base):
    """Webhook subscription for receiving validation events."""

    __tablename__ = "webhook_subscriptions"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # Webhook configuration
    url: Mapped[str] = mapped_column(String(2048))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Events to subscribe to (stored as array)
    events: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)),
        default=["validation.completed"]
    )

    # Security
    secret: Mapped[str] = mapped_column(String(100))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Statistics
    total_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    successful_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    failed_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="webhooks")
    deliveries = relationship(
        "WebhookDelivery",
        back_populates="subscription",
        cascade="all, delete-orphan",
        order_by="WebhookDelivery.created_at.desc()"
    )

    def is_subscribed_to(self, event_type: str) -> bool:
        """Check if subscription includes this event type."""
        return event_type in self.events or "validation.completed" in self.events

    @classmethod
    def create(
        cls,
        user_id: UUID,
        url: str,
        events: list[str],
        description: str | None = None,
    ) -> tuple["WebhookSubscription", str]:
        """Create a new webhook subscription.

        Returns the subscription and the raw secret (only shown once).
        """
        secret = generate_webhook_secret()

        subscription = cls(
            user_id=user_id,
            url=url,
            events=events,
            description=description,
            secret=secret,
        )

        return subscription, secret


class WebhookDelivery(Base):
    """Record of a webhook delivery attempt."""

    __tablename__ = "webhook_deliveries"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    subscription_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
        index=True,
    )

    # Event details
    event_type: Mapped[str] = mapped_column(String(50))
    event_id: Mapped[str] = mapped_column(String(64))
    payload: Mapped[str] = mapped_column(Text)

    # Delivery status
    status: Mapped[str] = mapped_column(String(20), default=DeliveryStatus.PENDING.value)

    # Retry tracking
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=4)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Response details
    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationship
    subscription = relationship("WebhookSubscription", back_populates="deliveries")

    # Retry schedule in minutes
    RETRY_SCHEDULE = [1, 5, 30, 120]

    def calculate_next_retry(self) -> datetime | None:
        """Calculate next retry time using exponential backoff.

        Retry schedule: 1min, 5min, 30min, 2hr
        """
        if self.attempt_count >= self.max_attempts:
            return None

        index = min(self.attempt_count, len(self.RETRY_SCHEDULE) - 1)
        return datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=self.RETRY_SCHEDULE[index])

    def mark_success(
        self,
        status_code: int,
        response_body: str | None,
        response_time_ms: int
    ) -> None:
        """Mark delivery as successful."""
        self.status = DeliveryStatus.SUCCESS.value
        self.response_status_code = status_code
        self.response_body = response_body[:5000] if response_body else None
        self.response_time_ms = response_time_ms
        self.completed_at = datetime.now(UTC).replace(tzinfo=None)
        self.last_attempt_at = datetime.now(UTC).replace(tzinfo=None)

    def mark_failed(
        self,
        error: str,
        status_code: int | None = None,
        response_body: str | None = None
    ) -> None:
        """Mark delivery attempt as failed and schedule retry if possible."""
        self.attempt_count += 1
        self.last_attempt_at = datetime.now(UTC).replace(tzinfo=None)
        self.response_status_code = status_code
        self.response_body = response_body[:5000] if response_body else None
        self.error_message = error[:1000] if error else None

        if self.attempt_count >= self.max_attempts:
            self.status = DeliveryStatus.FAILED.value
            self.completed_at = datetime.now(UTC).replace(tzinfo=None)
        else:
            self.status = DeliveryStatus.RETRYING.value
            self.next_retry_at = self.calculate_next_retry()
