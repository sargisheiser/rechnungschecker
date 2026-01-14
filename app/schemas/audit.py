"""Pydantic schemas for audit logging."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.audit import AuditAction


class AuditLogResponse(BaseModel):
    """Response for a single audit log entry."""

    id: UUID
    user_id: UUID
    action: AuditAction
    resource_type: str
    resource_id: str | None
    ip_address: str | None
    user_agent: str | None
    details: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogList(BaseModel):
    """Paginated list of audit logs."""

    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditLogQuery(BaseModel):
    """Query parameters for audit logs."""

    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)
    action: AuditAction | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class AuditExportQuery(BaseModel):
    """Query parameters for audit log export."""

    date_from: datetime | None = None
    date_to: datetime | None = None
    format: str = Field(default="json", pattern="^(json|csv)$")


class AuditActivitySummary(BaseModel):
    """Summary of user activity."""

    total_actions: int
    by_action: dict[str, int]
    period_days: int
