"""Validation log model for analytics."""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FileType(str, enum.Enum):
    """Type of invoice file validated."""

    XRECHNUNG = "xrechnung"
    ZUGFERD = "zugferd"


class ValidationLog(Base):
    """Validation log for tracking user validation history."""

    __tablename__ = "validation_logs"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    client_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Validation details (no content stored)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[FileType] = mapped_column(
        Enum(FileType, name='filetype', values_callable=lambda x: [e.value for e in x])
    )
    file_hash: Mapped[str] = mapped_column(String(64))  # SHA256
    file_size_bytes: Mapped[int] = mapped_column(Integer)

    # Results
    is_valid: Mapped[bool] = mapped_column(Boolean)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    info_count: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    xrechnung_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    zugferd_profile: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # User notes
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Performance
    processing_time_ms: Mapped[int] = mapped_column(Integer)
    validator_version: Mapped[str] = mapped_column(String(20))

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )

    # Relationships
    client = relationship("Client", back_populates="validations")
