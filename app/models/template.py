"""Template model for storing reusable sender/receiver data."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TemplateType(str, Enum):
    """Template type enum."""

    SENDER = "sender"
    RECEIVER = "receiver"


class Template(Base):
    """Template for storing frequently used sender/receiver company data.

    Users can save templates to quickly pre-fill invoice conversion forms
    with commonly used company information.
    """

    __tablename__ = "templates"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # Template identification
    name: Mapped[str] = mapped_column(String(100))  # e.g., "My Company", "Client ABC"
    template_type: Mapped[TemplateType] = mapped_column(
        SQLEnum(TemplateType, values_callable=lambda x: [e.value for e in x])
    )

    # Company information
    company_name: Mapped[str] = mapped_column(String(200))
    street: Mapped[str | None] = mapped_column(String(200), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), default="DE")

    # Tax information
    vat_id: Mapped[str | None] = mapped_column(String(20), nullable=True)  # USt-IdNr.
    tax_id: Mapped[str | None] = mapped_column(String(30), nullable=True)  # Steuernummer

    # Contact information
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Bank details (primarily for sender templates)
    iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    bic: Mapped[str | None] = mapped_column(String(11), nullable=True)

    # Default template flag
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="templates")
