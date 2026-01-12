"""Pydantic schemas for API key management."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    """Request to create a new API key."""

    name: str = Field(..., min_length=1, max_length=100, description="Name for the API key")
    description: str | None = Field(None, max_length=500, description="Optional description")
    expires_in_days: int | None = Field(None, ge=1, le=365, description="Days until expiration (null = never)")


class APIKeyResponse(BaseModel):
    """API key information (without the actual key)."""

    id: UUID
    name: str
    description: str | None
    key_prefix: str
    is_active: bool
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None
    usage_count: int
    requests_this_month: int


class APIKeyCreated(APIKeyResponse):
    """Response when creating a new API key (includes the actual key)."""

    key: str = Field(..., description="The API key - only shown once at creation!")


class APIKeyList(BaseModel):
    """List of API keys for a user."""

    items: list[APIKeyResponse]
    total: int
    max_keys: int
    api_calls_limit: int
    api_calls_used: int


class APIKeyUpdate(BaseModel):
    """Request to update an API key."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    is_active: bool | None = None
