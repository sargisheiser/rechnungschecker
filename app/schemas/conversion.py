"""Schemas for PDF to e-invoice conversion."""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class OutputFormat(StrEnum):
    """Supported output formats."""

    XRECHNUNG = "xrechnung"
    ZUGFERD = "zugferd"


class ZUGFeRDProfile(StrEnum):
    """ZUGFeRD profile levels."""

    MINIMUM = "MINIMUM"
    BASIC = "BASIC"
    EN16931 = "EN16931"
    EXTENDED = "EXTENDED"


class AddressSchema(BaseModel):
    """Address data."""

    name: str
    street: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country_code: str = "DE"


class LineItemSchema(BaseModel):
    """Invoice line item."""

    description: str
    quantity: Decimal = Decimal("1")
    unit: str = "C62"  # Default unit code (piece)
    unit_price: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("19")
    total: Decimal = Decimal("0")


class ExtractedDataSchema(BaseModel):
    """Extracted invoice data for preview/editing."""

    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    delivery_date: date | None = None

    seller_name: str | None = None
    seller_street: str | None = None
    seller_postal_code: str | None = None
    seller_city: str | None = None
    seller_vat_id: str | None = None
    seller_tax_id: str | None = None

    buyer_name: str | None = None
    buyer_street: str | None = None
    buyer_postal_code: str | None = None
    buyer_city: str | None = None
    buyer_reference: str | None = None

    net_amount: Decimal | None = None
    vat_amount: Decimal | None = None
    gross_amount: Decimal | None = None
    currency: str = "EUR"

    iban: str | None = None
    bic: str | None = None
    bank_name: str | None = None
    payment_reference: str | None = None

    leitweg_id: str | None = None
    order_reference: str | None = None

    confidence: float = Field(default=0.0, ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)


class ConversionRequest(BaseModel):
    """Request for conversion with optional data overrides."""

    output_format: OutputFormat = OutputFormat.XRECHNUNG
    zugferd_profile: ZUGFeRDProfile = ZUGFeRDProfile.EN16931
    embed_in_pdf: bool = True

    # Optional overrides for extracted data
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    delivery_date: date | None = None

    seller_name: str | None = None
    seller_street: str | None = None
    seller_postal_code: str | None = None
    seller_city: str | None = None
    seller_vat_id: str | None = None

    buyer_name: str | None = None
    buyer_street: str | None = None
    buyer_postal_code: str | None = None
    buyer_city: str | None = None
    buyer_reference: str | None = None

    net_amount: Decimal | None = None
    vat_amount: Decimal | None = None
    gross_amount: Decimal | None = None

    iban: str | None = None
    bic: str | None = None
    leitweg_id: str | None = None


class ValidationErrorSchema(BaseModel):
    """Validation error/warning for conversion result."""

    severity: str
    code: str
    message_de: str
    message_en: str | None = None
    location: str | None = None
    suggestion: str | None = None


class ValidationResultSchema(BaseModel):
    """Simplified validation result for conversion response."""

    is_valid: bool
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    errors: list[ValidationErrorSchema] = Field(default_factory=list)
    warnings: list[ValidationErrorSchema] = Field(default_factory=list)
    infos: list[ValidationErrorSchema] = Field(default_factory=list)
    validator_version: str | None = None
    processing_time_ms: int | None = None


class ConversionResponse(BaseModel):
    """Response from conversion endpoint."""

    success: bool
    conversion_id: str
    filename: str
    output_format: OutputFormat
    extracted_data: ExtractedDataSchema
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    validation_result: ValidationResultSchema | None = None


class PreviewResponse(BaseModel):
    """Response from preview extraction endpoint."""

    extracted_data: ExtractedDataSchema
    ocr_used: bool
    ocr_available: bool
    ai_used: bool = False


class ConversionStatusResponse(BaseModel):
    """Conversion capabilities status."""

    ocr_available: bool
    ai_available: bool = False
    supported_formats: list[OutputFormat]
    supported_profiles: list[ZUGFeRDProfile]


class SendInvoiceEmailRequest(BaseModel):
    """Request to send converted invoice via email."""

    recipient_email: str | None = None
    send_copy_to_self: bool = False


class SendInvoiceEmailResponse(BaseModel):
    """Response from sending invoice email."""

    success: bool
    message: str
    emails_sent: int = 0
