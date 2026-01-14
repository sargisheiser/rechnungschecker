"""Client model for multi-tenant support (Steuerberater plan)."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Client(Base):
    """Client/Mandant for tax consultants to manage.

    Allows Steuerberater plan users to organize validations
    by client/company they are working for.
    """

    __tablename__ = "clients"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # Client information
    name: Mapped[str] = mapped_column(String(200))  # Company/client name
    client_number: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Internal reference number
    tax_number: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Steuernummer
    vat_id: Mapped[str | None] = mapped_column(String(20), nullable=True)  # USt-IdNr.

    # Contact information
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Address
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="DE")  # ISO country code

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Statistics (denormalized for performance)
    validation_count: Mapped[int] = mapped_column(Integer, default=0)
    last_validation_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="clients")
    validations = relationship("ValidationLog", back_populates="client", cascade="all, delete-orphan")
    batch_jobs = relationship("BatchJob", back_populates="client")

    def increment_validation_count(self) -> None:
        """Increment validation count and update last validation time."""
        self.validation_count += 1
        self.last_validation_at = datetime.utcnow()
