"""Pydantic schemas for validation endpoints."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Severity level of validation messages."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationError(BaseModel):
    """Single validation error/warning/info message."""

    severity: ValidationSeverity
    code: str = Field(description="KoSIT rule code, e.g., BR-DE-01")
    message_de: str = Field(description="German error message")
    message_en: str | None = Field(default=None, description="English error message")
    location: str | None = Field(default=None, description="XPath location in document")
    suggestion: str | None = Field(default=None, description="How to fix the issue")


class ValidationRequest(BaseModel):
    """Request metadata for validation."""

    filename: str
    file_size_bytes: int


class ValidationResponse(BaseModel):
    """Response from validation endpoint."""

    id: UUID = Field(description="Unique validation ID for report retrieval")
    is_valid: bool = Field(description="Whether the invoice passes all validation rules")
    file_type: str = Field(description="Detected file type: xrechnung or zugferd")
    file_hash: str = Field(description="SHA256 hash of uploaded file")

    # Counts
    error_count: int = Field(default=0)
    warning_count: int = Field(default=0)
    info_count: int = Field(default=0)

    # Detailed messages
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[ValidationError] = Field(default_factory=list)
    infos: list[ValidationError] = Field(default_factory=list)

    # Metadata
    xrechnung_version: str | None = Field(default=None)
    zugferd_profile: str | None = Field(default=None)
    validator_version: str = Field(description="KoSIT validator version used")
    processing_time_ms: int = Field(description="Processing time in milliseconds")
    validated_at: datetime = Field(default_factory=datetime.utcnow)

    # Report
    report_url: str | None = Field(default=None, description="URL to download PDF report")

    # Usage info (for authenticated users)
    validations_used: int | None = Field(default=None, description="Validations used this month")
    validations_limit: int | None = Field(default=None, description="Monthly validation limit (null = unlimited)")


class ValidationHistoryItem(BaseModel):
    """Single item in validation history."""

    id: UUID
    file_name: str | None = None
    file_type: str
    is_valid: bool
    error_count: int
    warning_count: int
    validated_at: datetime


class ValidationHistoryResponse(BaseModel):
    """List of past validations for a user."""

    items: list[ValidationHistoryItem]
    total: int
    page: int
    page_size: int


class GuestValidationResponse(ValidationResponse):
    """Response from guest validation endpoint with usage tracking."""

    guest_id: str = Field(description="Guest identifier for tracking")
    validations_used: int = Field(description="Number of validations used by this guest")
    validations_limit: int = Field(description="Maximum validations allowed for guests")


class ValidationDetailResponse(BaseModel):
    """Detailed validation information for history view."""

    id: UUID
    file_name: str | None = None
    file_type: str
    file_hash: str
    is_valid: bool
    error_count: int
    warning_count: int
    info_count: int
    xrechnung_version: str | None = None
    zugferd_profile: str | None = None
    processing_time_ms: int
    validator_version: str
    notes: str | None = None
    validated_at: datetime


class UpdateNotesRequest(BaseModel):
    """Request to update validation notes."""

    notes: str | None = Field(default=None, max_length=2000)
