"""Extracted invoice data model for DATEV export."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExtractedInvoiceData(Base):
    """Extracted invoice data linked to validation results.

    Stores financial data extracted from validated invoices for use in
    DATEV Buchungsstapel exports and other accounting integrations.
    """

    __tablename__ = "extracted_invoice_data"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    validation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("validation_logs.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )

    # Invoice identifiers
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial totals (stored as Decimal for precision)
    net_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=15, scale=2), nullable=True
    )
    vat_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=15, scale=2), nullable=True
    )
    gross_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=15, scale=2), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    # Primary VAT rate (for simple single-rate invoices)
    # Multi-rate invoices will use the dominant rate
    vat_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=2), nullable=True
    )

    # Seller info (for Buchungstext in DATEV)
    seller_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # VAT breakdown for multi-rate invoices (JSON array)
    # Format: [{"rate": "19", "net_amount": "100.00", "vat_amount": "19.00"}, ...]
    vat_breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Extraction metadata
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(precision=3, scale=2), default=Decimal("1.0")
    )
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationship back to validation
    validation = relationship("ValidationLog", backref="extracted_data", uselist=False)
