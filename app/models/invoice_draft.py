"""Invoice draft model for the invoice creator wizard."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InvoiceDraft(Base):
    """Draft invoice for the invoice creator wizard."""

    __tablename__ = "invoice_drafts"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    client_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Draft metadata
    name: Mapped[str] = mapped_column(String(255), default="Neue Rechnung")
    output_format: Mapped[str] = mapped_column(
        String(20), default="xrechnung"
    )  # "xrechnung" or "zugferd"

    # Invoice data as structured JSON
    # Contains: seller, buyer, line_items, payment, delivery, tax_info, references, notes
    invoice_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Wizard progress
    current_step: Mapped[int] = mapped_column(Integer, default=1)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)

    # Generated output
    generated_xml: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_result_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User")
    client = relationship("Client")
