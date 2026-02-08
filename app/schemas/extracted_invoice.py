"""Pydantic schemas for extracted invoice data."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ExtractedInvoiceDataCreate(BaseModel):
    """Schema for creating extracted invoice data."""

    invoice_number: str | None = None
    invoice_date: date | None = None
    net_amount: Decimal | None = None
    vat_amount: Decimal | None = None
    gross_amount: Decimal | None = None
    currency: str = "EUR"
    vat_rate: Decimal | None = None
    seller_name: str | None = None
    confidence: Decimal = Field(default=Decimal("1.0"), ge=0, le=1)


class ExtractedInvoiceDataResponse(BaseModel):
    """Schema for extracted invoice data response."""

    id: UUID
    validation_id: UUID
    invoice_number: str | None
    invoice_date: date | None
    net_amount: Decimal | None
    vat_amount: Decimal | None
    gross_amount: Decimal | None
    currency: str
    vat_rate: Decimal | None
    seller_name: str | None
    confidence: Decimal
    extracted_at: datetime

    model_config = {"from_attributes": True}
