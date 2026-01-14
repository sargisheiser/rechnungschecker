"""Integration settings model for third-party services."""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class IntegrationType(str, enum.Enum):
    """Supported integration types."""

    LEXOFFICE = "lexoffice"
    SLACK = "slack"
    TEAMS = "teams"


class IntegrationSettings(Base):
    """User integration settings for third-party services.

    Stores encrypted credentials and notification preferences
    for Lexoffice, Slack, and Teams integrations.
    """

    __tablename__ = "integration_settings"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Integration type
    integration_type: Mapped[IntegrationType] = mapped_column(
        Enum(IntegrationType, name="integrationtype", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    # Status
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Encrypted credentials/config (stored as encrypted JSON)
    # For Lexoffice: {"api_key": "..."}
    # For Slack: {"webhook_url": "..."}
    # For Teams: {"webhook_url": "..."}
    encrypted_config: Mapped[str] = mapped_column(Text, nullable=False)

    # Notification settings (for Slack/Teams)
    notify_on_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_invalid: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_warning: Mapped[bool] = mapped_column(Boolean, default=True)

    # Statistics
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    successful_requests: Mapped[int] = mapped_column(Integer, default=0)
    failed_requests: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    user = relationship("User", back_populates="integrations")

    # Unique constraint: one integration type per user
    __table_args__ = (
        Index(
            "ix_integration_user_type",
            "user_id",
            "integration_type",
            unique=True,
        ),
    )

    def record_request(self, success: bool) -> None:
        """Record a request to this integration.

        Args:
            success: Whether the request was successful
        """
        self.last_used_at = datetime.utcnow()
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
