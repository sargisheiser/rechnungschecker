"""Schemas for CSV export functionality."""

from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    """Export format options."""

    CSV_DATEV = "datev"  # Semicolon delimiter, German headers
    CSV_EXCEL = "excel"  # Comma delimiter, German headers


class ValidationStatus(str, Enum):
    """Filter for validation status."""

    ALL = "all"
    VALID = "valid"
    INVALID = "invalid"


class ValidationsExportParams(BaseModel):
    """Query parameters for validations export."""

    client_id: UUID | None = Field(default=None, description="Filter by client ID")
    date_from: date | None = Field(default=None, description="Start date (inclusive)")
    date_to: date | None = Field(default=None, description="End date (inclusive)")
    status: ValidationStatus = Field(default=ValidationStatus.ALL, description="Filter by validation status")
    format: ExportFormat = Field(default=ExportFormat.CSV_DATEV, description="Export format")


class ClientsExportParams(BaseModel):
    """Query parameters for clients export."""

    include_inactive: bool = Field(default=False, description="Include inactive clients")
    date_from: date | None = Field(default=None, description="Filter validations from date")
    date_to: date | None = Field(default=None, description="Filter validations to date")
    format: ExportFormat = Field(default=ExportFormat.CSV_DATEV, description="Export format")
