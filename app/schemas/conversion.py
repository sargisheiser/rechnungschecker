"""Schemas for PDF to e-invoice conversion."""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    """Supported output formats."""

    XRECHNUNG = "xrechnung"
    ZUGFERD = "zugferd"


class ZUGFeRDProfile(str, Enum):
    """ZUGFeRD profile levels."""

    MINIMUM = "MINIMUM"
    BASIC = "BASIC"
    EN16931 = "EN16931"
    EXTENDED = "EXTENDED"


class AddressSchema(BaseModel):
    """Address data."""

    name: str
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country_code: str = "DE"


class LineItemSchema(BaseModel):
    """Invoice line item."""

    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("19")
    total: Decimal = Decimal("0")


class ExtractedDataSchema(BaseModel):
    """Extracted invoice data for preview/editing."""

    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    delivery_date: Optional[date] = None

    seller_name: Optional[str] = None
    seller_street: Optional[str] = None
    seller_postal_code: Optional[str] = None
    seller_city: Optional[str] = None
    seller_vat_id: Optional[str] = None
    seller_tax_id: Optional[str] = None

    buyer_name: Optional[str] = None
    buyer_street: Optional[str] = None
    buyer_postal_code: Optional[str] = None
    buyer_city: Optional[str] = None
    buyer_reference: Optional[str] = None

    net_amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None
    currency: str = "EUR"

    iban: Optional[str] = None
    bic: Optional[str] = None
    bank_name: Optional[str] = None
    payment_reference: Optional[str] = None

    leitweg_id: Optional[str] = None
    order_reference: Optional[str] = None

    confidence: float = Field(default=0.0, ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)


class ConversionRequest(BaseModel):
    """Request for conversion with optional data overrides."""

    output_format: OutputFormat = OutputFormat.XRECHNUNG
    zugferd_profile: ZUGFeRDProfile = ZUGFeRDProfile.EN16931
    embed_in_pdf: bool = True

    # Optional overrides for extracted data
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    delivery_date: Optional[date] = None

    seller_name: Optional[str] = None
    seller_street: Optional[str] = None
    seller_postal_code: Optional[str] = None
    seller_city: Optional[str] = None
    seller_vat_id: Optional[str] = None

    buyer_name: Optional[str] = None
    buyer_street: Optional[str] = None
    buyer_postal_code: Optional[str] = None
    buyer_city: Optional[str] = None
    buyer_reference: Optional[str] = None

    net_amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None

    iban: Optional[str] = None
    bic: Optional[str] = None
    leitweg_id: Optional[str] = None


class ValidationErrorSchema(BaseModel):
    """Validation error/warning for conversion result."""

    severity: str
    code: str
    message_de: str
    message_en: Optional[str] = None
    location: Optional[str] = None
    suggestion: Optional[str] = None


class ValidationResultSchema(BaseModel):
    """Simplified validation result for conversion response."""

    is_valid: bool
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    errors: list[ValidationErrorSchema] = Field(default_factory=list)
    warnings: list[ValidationErrorSchema] = Field(default_factory=list)
    infos: list[ValidationErrorSchema] = Field(default_factory=list)
    validator_version: Optional[str] = None
    processing_time_ms: Optional[int] = None


class ConversionResponse(BaseModel):
    """Response from conversion endpoint."""

    success: bool
    conversion_id: str
    filename: str
    output_format: OutputFormat
    extracted_data: ExtractedDataSchema
    warnings: list[str] = Field(default_factory=list)
    error: Optional[str] = None
    validation_result: Optional[ValidationResultSchema] = None


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
