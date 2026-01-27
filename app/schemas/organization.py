"""Pydantic schemas for organization endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationCreate(BaseModel):
    """Schema for creating an organization."""

    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(None, max_length=1000)


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = Field(None, max_length=1000)


class OrganizationResponse(BaseModel):
    """Schema for organization response."""

    id: UUID
    name: str
    slug: str
    description: str | None
    owner_id: UUID
    plan: str
    max_members: int
    is_active: bool
    validations_this_month: int
    conversions_this_month: int
    member_count: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(BaseModel):
    """Schema for listing organizations."""

    organizations: list[OrganizationResponse]
    total: int


class MemberInvite(BaseModel):
    """Schema for inviting a member."""

    email: EmailStr
    role: str = Field(default="member", pattern="^(admin|member)$")


class MemberUpdate(BaseModel):
    """Schema for updating a member's role."""

    role: str = Field(pattern="^(admin|member)$")


class MemberResponse(BaseModel):
    """Schema for member response."""

    id: UUID
    user_id: UUID
    email: str
    full_name: str | None
    role: str
    invited_at: datetime
    joined_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class MemberListResponse(BaseModel):
    """Schema for listing members."""

    members: list[MemberResponse]
    total: int


class InvitationResponse(BaseModel):
    """Schema for invitation response."""

    id: UUID
    email: str
    role: str
    organization_name: str
    expires_at: datetime
    is_valid: bool

    model_config = ConfigDict(from_attributes=True)


class InvitationAccept(BaseModel):
    """Schema for accepting an invitation."""

    token: str
