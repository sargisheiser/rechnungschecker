"""Audit logging model for tracking user actions."""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditAction(str, enum.Enum):
    """Types of actions that can be audited."""

    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    PASSWORD_CHANGE = "password_change"

    # Validation
    VALIDATE = "validate"
    VALIDATE_BATCH = "validate_batch"

    # Conversion
    CONVERT = "convert"

    # API Keys
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"

    # Clients
    CLIENT_CREATE = "client_create"
    CLIENT_UPDATE = "client_update"
    CLIENT_DELETE = "client_delete"

    # Webhooks
    WEBHOOK_CREATE = "webhook_create"
    WEBHOOK_UPDATE = "webhook_update"
    WEBHOOK_DELETE = "webhook_delete"

    # Integrations
    INTEGRATION_CREATE = "integration_create"
    INTEGRATION_UPDATE = "integration_update"
    INTEGRATION_DELETE = "integration_delete"

    # Export
    EXPORT_DATA = "export_data"

    # Settings
    SETTINGS_UPDATE = "settings_update"


class AuditLog(Base):
    """Audit log entry for tracking user actions."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="auditaction", values_callable=lambda x: [e.value for e in x], create_type=False)
    )
    resource_type: Mapped[str] = mapped_column(String(50))
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )

    # Relationships
    user = relationship("User", backref="audit_logs")

    def to_dict(self) -> dict:
        """Convert audit log to dictionary for export."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "action": self.action.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
