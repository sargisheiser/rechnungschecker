"""Pydantic schemas for templates."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.template import TemplateType


class TemplateCreate(BaseModel):
    """Request to create a new template."""

    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    template_type: TemplateType = Field(..., description="sender or receiver")

    # Company information
    company_name: str = Field(..., min_length=1, max_length=200, description="Company name")
    street: str | None = Field(None, max_length=200)
    postal_code: str | None = Field(None, max_length=20)
    city: str | None = Field(None, max_length=100)
    country_code: str = Field(default="DE", min_length=2, max_length=2)

    # Tax information
    vat_id: str | None = Field(None, max_length=20, description="USt-IdNr.")
    tax_id: str | None = Field(None, max_length=30, description="Steuernummer")

    # Contact information
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)

    # Bank details (primarily for sender)
    iban: str | None = Field(None, max_length=34)
    bic: str | None = Field(None, max_length=11)

    # Default flag
    is_default: bool = False


class TemplateUpdate(BaseModel):
    """Request to update a template."""

    name: str | None = Field(None, min_length=1, max_length=100)
    template_type: TemplateType | None = None

    company_name: str | None = Field(None, min_length=1, max_length=200)
    street: str | None = Field(None, max_length=200)
    postal_code: str | None = Field(None, max_length=20)
    city: str | None = Field(None, max_length=100)
    country_code: str | None = Field(None, min_length=2, max_length=2)

    vat_id: str | None = Field(None, max_length=20)
    tax_id: str | None = Field(None, max_length=30)

    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)

    iban: str | None = Field(None, max_length=34)
    bic: str | None = Field(None, max_length=11)

    is_default: bool | None = None


class TemplateResponse(BaseModel):
    """Template information response."""

    id: UUID
    name: str
    template_type: TemplateType

    company_name: str
    street: str | None
    postal_code: str | None
    city: str | None
    country_code: str

    vat_id: str | None
    tax_id: str | None

    email: str | None
    phone: str | None

    iban: str | None
    bic: str | None

    is_default: bool

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TemplateListItem(BaseModel):
    """Simplified template info for list views."""

    id: UUID
    name: str
    template_type: TemplateType
    company_name: str
    city: str | None
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TemplateList(BaseModel):
    """Paginated list of templates."""

    items: list[TemplateListItem]
    total: int
    page: int
    page_size: int
