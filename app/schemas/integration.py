"""Schemas for third-party integrations."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


class IntegrationType(str, Enum):
    """Supported integration types."""

    LEXOFFICE = "lexoffice"
    SLACK = "slack"
    TEAMS = "teams"


# --- Lexoffice schemas ---


class LexofficeConfig(BaseModel):
    """Configuration for Lexoffice integration."""

    api_key: str = Field(..., min_length=10, description="Lexoffice API key")


class LexofficeInvoiceListItem(BaseModel):
    """Invoice item in list response."""

    id: str
    voucher_number: str | None = Field(None, alias="voucherNumber")
    voucher_date: str | None = Field(None, alias="voucherDate")
    total_amount: float | None = Field(None, alias="totalAmount")
    status: str | None = None

    class Config:
        populate_by_name = True


class LexofficeInvoiceList(BaseModel):
    """List of invoices from Lexoffice."""

    content: list[LexofficeInvoiceListItem] = []
    total_pages: int = Field(0, alias="totalPages")
    total_elements: int = Field(0, alias="totalElements")
    page: int = 0

    class Config:
        populate_by_name = True


class LexofficeFetchRequest(BaseModel):
    """Request to fetch and validate invoices from Lexoffice."""

    invoice_ids: list[str] = Field(..., min_length=1, max_length=10)


class LexofficeFetchResult(BaseModel):
    """Result of fetching and validating an invoice."""

    invoice_id: str
    voucher_number: str | None = None
    validation_id: UUID | None = None
    is_valid: bool | None = None
    error_count: int = 0
    warning_count: int = 0
    error_message: str | None = None


# --- Notification schemas ---


class NotificationConfig(BaseModel):
    """Configuration for Slack/Teams notification integration."""

    webhook_url: HttpUrl = Field(..., description="Incoming webhook URL")

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v):
        url_str = str(v)
        # Basic validation for Slack webhook URL format
        if "slack.com" in url_str and "/services/" not in url_str:
            raise ValueError("Ungueltiges Slack Webhook URL Format")
        return v


class NotificationSettings(BaseModel):
    """Notification settings for an integration."""

    notify_on_valid: bool = True
    notify_on_invalid: bool = True
    notify_on_warning: bool = True


# --- Integration CRUD schemas ---


class IntegrationCreate(BaseModel):
    """Request to create/update an integration."""

    config: dict = Field(..., description="Type-specific configuration (api_key or webhook_url)")
    notify_on_valid: bool = True
    notify_on_invalid: bool = True
    notify_on_warning: bool = True


class IntegrationUpdate(BaseModel):
    """Request to update integration settings."""

    is_enabled: bool | None = None
    notify_on_valid: bool | None = None
    notify_on_invalid: bool | None = None
    notify_on_warning: bool | None = None


class IntegrationResponse(BaseModel):
    """Integration settings response."""

    id: UUID
    integration_type: IntegrationType
    is_enabled: bool
    notify_on_valid: bool
    notify_on_invalid: bool
    notify_on_warning: bool
    # Statistics
    last_used_at: datetime | None
    total_requests: int
    successful_requests: int
    failed_requests: int
    # Timestamps
    created_at: datetime
    updated_at: datetime
    # Masked config info (e.g., "api_key: abc1...xyz9")
    config_hint: str | None = None


class IntegrationList(BaseModel):
    """List of user integrations."""

    items: list[IntegrationResponse]


class IntegrationTestResponse(BaseModel):
    """Response from testing an integration."""

    success: bool
    message: str
