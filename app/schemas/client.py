"""Pydantic schemas for client management."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


class ClientCreate(BaseModel):
    """Request to create a new client."""

    name: str = Field(..., min_length=1, max_length=200, description="Company/client name")
    client_number: str | None = Field(None, max_length=50, description="Internal reference number")
    tax_number: str | None = Field(None, max_length=50, description="Steuernummer")
    vat_id: str | None = Field(None, max_length=20, description="USt-IdNr.")

    # Contact
    contact_name: str | None = Field(None, max_length=200)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(None, max_length=50)

    # Address
    street: str | None = Field(None, max_length=255)
    postal_code: str | None = Field(None, max_length=10)
    city: str | None = Field(None, max_length=100)
    country: str = Field(default="DE", min_length=2, max_length=2)

    # Notes
    notes: str | None = Field(None, max_length=2000)


class ClientUpdate(BaseModel):
    """Request to update a client."""

    name: str | None = Field(None, min_length=1, max_length=200)
    client_number: str | None = Field(None, max_length=50)
    tax_number: str | None = Field(None, max_length=50)
    vat_id: str | None = Field(None, max_length=20)

    contact_name: str | None = Field(None, max_length=200)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(None, max_length=50)

    street: str | None = Field(None, max_length=255)
    postal_code: str | None = Field(None, max_length=10)
    city: str | None = Field(None, max_length=100)
    country: str | None = Field(None, min_length=2, max_length=2)

    notes: str | None = Field(None, max_length=2000)
    is_active: bool | None = None


class ClientResponse(BaseModel):
    """Client information response."""

    id: UUID
    name: str
    client_number: str | None
    tax_number: str | None
    vat_id: str | None

    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None

    street: str | None
    postal_code: str | None
    city: str | None
    country: str

    notes: str | None
    is_active: bool

    validation_count: int
    last_validation_at: datetime | None

    created_at: datetime
    updated_at: datetime


class ClientListItem(BaseModel):
    """Simplified client info for list views."""

    id: UUID
    name: str
    client_number: str | None
    is_active: bool
    validation_count: int
    last_validation_at: datetime | None
    created_at: datetime


class ClientList(BaseModel):
    """Paginated list of clients."""

    items: list[ClientListItem]
    total: int
    page: int
    page_size: int
    max_clients: int


class ClientStats(BaseModel):
    """Client statistics for dashboard."""

    total_clients: int
    active_clients: int
    total_validations: int
    max_clients: int
