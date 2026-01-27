"""Pydantic schemas for invoice creator endpoints."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PartyAddress(BaseModel):
    """Address for seller or buyer."""

    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str = "DE"


class PartyInfo(BaseModel):
    """Party (seller or buyer) information."""

    name: str
    address: PartyAddress | None = None
    tax_id: str | None = None  # Steuernummer
    vat_id: str | None = None  # USt-IdNr
    email: str | None = None
    phone: str | None = None
    iban: str | None = None
    bic: str | None = None
    bank_name: str | None = None


class LineItem(BaseModel):
    """Invoice line item."""

    id: str | None = None
    description: str
    quantity: Decimal = Decimal("1")
    unit: str = "STK"  # C62=Piece, H=Hour, DAY=Day
    unit_price: Decimal
    tax_rate: Decimal = Decimal("19")  # 19%, 7%, or 0%
    tax_category: str = "S"  # S=Standard, Z=Zero, E=Exempt


class PaymentInfo(BaseModel):
    """Payment information."""

    payment_terms: str | None = None
    payment_means_code: str = "58"  # 58=SEPA Credit Transfer
    due_date: date | None = None
    iban: str | None = None
    bic: str | None = None
    bank_name: str | None = None


class InvoiceReferences(BaseModel):
    """Invoice references."""

    order_reference: str | None = None
    buyer_reference: str | None = None  # Leitweg-ID for XRechnung
    contract_reference: str | None = None
    project_reference: str | None = None


class InvoiceData(BaseModel):
    """Complete invoice data structure."""

    # Header
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    currency: str = "EUR"

    # Parties
    seller: PartyInfo | None = None
    buyer: PartyInfo | None = None

    # Line items
    line_items: list[LineItem] = []

    # Payment
    payment: PaymentInfo | None = None

    # References
    references: InvoiceReferences | None = None

    # Notes
    note: str | None = None


class InvoiceDraftCreate(BaseModel):
    """Schema for creating a draft invoice."""

    name: str = Field(default="Neue Rechnung", max_length=255)
    output_format: str = Field(default="xrechnung", pattern="^(xrechnung|zugferd)$")
    client_id: UUID | None = None


class InvoiceDraftUpdate(BaseModel):
    """Schema for updating a draft invoice."""

    name: str | None = Field(None, max_length=255)
    output_format: str | None = Field(None, pattern="^(xrechnung|zugferd)$")
    current_step: int | None = Field(None, ge=1, le=7)
    invoice_data: InvoiceData | None = None


class InvoiceDraftResponse(BaseModel):
    """Schema for invoice draft response."""

    id: UUID
    user_id: UUID
    client_id: UUID | None
    name: str
    output_format: str
    invoice_data: InvoiceData
    current_step: int
    is_complete: bool
    generated_xml: str | None
    validation_result_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceDraftListItem(BaseModel):
    """Schema for listing invoice drafts."""

    id: UUID
    name: str
    output_format: str
    current_step: int
    is_complete: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceDraftList(BaseModel):
    """Schema for list of invoice drafts."""

    drafts: list[InvoiceDraftListItem]
    total: int


class GenerateInvoiceResponse(BaseModel):
    """Schema for generated invoice response."""

    id: UUID
    xml: str
    is_valid: bool
    validation_errors: list[str] = []
    validation_warnings: list[str] = []
