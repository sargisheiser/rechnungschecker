"""Pydantic schemas for webhook management."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


class WebhookEventType(str, Enum):
    """Webhook event types."""

    VALIDATION_COMPLETED = "validation.completed"
    VALIDATION_VALID = "validation.valid"
    VALIDATION_INVALID = "validation.invalid"
    VALIDATION_WARNING = "validation.warning"


class DeliveryStatus(str, Enum):
    """Webhook delivery status."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


# --- Request schemas ---


class WebhookCreate(BaseModel):
    """Request to create a new webhook subscription."""

    url: HttpUrl = Field(..., description="HTTPS endpoint URL to receive webhook events")
    events: list[WebhookEventType] = Field(
        default=[WebhookEventType.VALIDATION_COMPLETED],
        description="Events to subscribe to",
        min_length=1,
    )
    description: str | None = Field(
        None,
        max_length=500,
        description="Optional description"
    )

    @field_validator("url")
    @classmethod
    def validate_https(cls, v):
        """Ensure URL uses HTTPS in production."""
        url_str = str(v)
        if not url_str.startswith("https://"):
            # Allow localhost for development
            if not any(host in url_str for host in ["localhost", "127.0.0.1"]):
                raise ValueError("Webhook URL must use HTTPS")
        return v


class WebhookUpdate(BaseModel):
    """Request to update a webhook subscription."""

    url: HttpUrl | None = None
    events: list[WebhookEventType] | None = Field(None, min_length=1)
    description: str | None = Field(None, max_length=500)
    is_active: bool | None = None


# --- Response schemas ---


class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery record."""

    id: UUID
    event_type: str
    event_id: str
    status: DeliveryStatus
    attempt_count: int
    response_status_code: int | None
    response_time_ms: int | None
    error_message: str | None
    created_at: datetime
    last_attempt_at: datetime | None
    completed_at: datetime | None


class WebhookResponse(BaseModel):
    """Webhook subscription information."""

    id: UUID
    url: str
    events: list[str]
    description: str | None
    is_active: bool

    # Statistics
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    last_triggered_at: datetime | None
    last_success_at: datetime | None

    # Timestamps
    created_at: datetime
    updated_at: datetime


class WebhookCreated(WebhookResponse):
    """Response when creating a new webhook (includes secret)."""

    secret: str = Field(
        ...,
        description="Webhook signing secret - only shown once at creation!"
    )


class WebhookWithDeliveries(WebhookResponse):
    """Webhook with recent delivery history."""

    recent_deliveries: list[WebhookDeliveryResponse] = Field(
        default_factory=list,
        description="Recent delivery attempts (last 20)"
    )


class WebhookList(BaseModel):
    """List of webhooks for a user."""

    items: list[WebhookResponse]
    total: int
    max_webhooks: int


class WebhookTestResponse(BaseModel):
    """Response from webhook test endpoint."""

    success: bool
    delivery_id: UUID
    message: str
    response_status_code: int | None = None
    response_time_ms: int | None = None


# --- Webhook payload schemas ---


class ValidationEventPayload(BaseModel):
    """Payload sent to webhook endpoints."""

    event_type: str = Field(description="Event type, e.g., validation.completed")
    event_id: str = Field(description="Unique event ID for idempotency")
    timestamp: datetime = Field(description="When the event occurred")

    # Validation data
    validation_id: UUID
    file_name: str | None
    file_type: str  # xrechnung or zugferd
    file_hash: str

    is_valid: bool
    error_count: int
    warning_count: int
    info_count: int

    xrechnung_version: str | None = None
    zugferd_profile: str | None = None

    processing_time_ms: int
    validated_at: datetime

    # Optional client context (for Steuerberater)
    client_id: UUID | None = None
    client_name: str | None = None
