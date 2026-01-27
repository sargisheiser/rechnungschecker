"""Pydantic schemas for admin endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AdminUserListItem(BaseModel):
    """Schema for user in admin list view."""

    id: UUID
    email: str
    full_name: str | None = None
    company_name: str | None = None
    plan: str
    is_active: bool
    is_verified: bool
    is_admin: bool
    validations_this_month: int
    conversions_this_month: int
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserDetail(BaseModel):
    """Schema for full user details in admin view."""

    id: UUID
    email: str
    full_name: str | None = None
    company_name: str | None = None
    plan: str
    is_active: bool
    is_verified: bool
    is_admin: bool
    validations_this_month: int
    conversions_this_month: int
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    plan_valid_until: datetime | None = None
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None

    # Notification preferences
    email_notifications: bool
    notify_validation_results: bool
    notify_weekly_summary: bool
    notify_marketing: bool

    model_config = ConfigDict(from_attributes=True)


class AdminUserUpdate(BaseModel):
    """Schema for admin updating a user."""

    is_active: bool | None = None
    is_verified: bool | None = None
    is_admin: bool | None = None
    plan: str | None = Field(None, pattern="^(free|starter|pro|steuerberater)$")
    full_name: str | None = Field(None, max_length=255)
    company_name: str | None = Field(None, max_length=255)


class AdminUserList(BaseModel):
    """Schema for paginated user list."""

    items: list[AdminUserListItem]
    total: int
    page: int
    page_size: int


class PlatformStats(BaseModel):
    """Schema for platform-wide statistics."""

    total_users: int
    active_users: int
    verified_users: int
    total_validations: int
    total_conversions: int
    validations_today: int
    validations_this_week: int
    validations_this_month: int
    users_by_plan: dict[str, int]
    recent_registrations: list[AdminUserListItem]


class AdminAuditLogItem(BaseModel):
    """Schema for audit log item in admin view."""

    id: UUID
    user_id: UUID
    user_email: str | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    details: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminAuditLogList(BaseModel):
    """Schema for paginated audit log list."""

    items: list[AdminAuditLogItem]
    total: int
    page: int
    page_size: int
