"""Audit log API endpoints for viewing and exporting user activity."""

import csv
import io
from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, DbSession
from app.models.audit import AuditAction
from app.schemas.audit import (
    AuditActivitySummary,
    AuditLogList,
    AuditLogResponse,
)
from app.services.audit import AuditService

router = APIRouter()


@router.get("/logs", response_model=AuditLogList)
async def get_audit_logs(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=50, ge=1, le=100, description="Items per page"),
    action: Optional[AuditAction] = Query(default=None, description="Filter by action type"),
    date_from: Optional[datetime] = Query(default=None, description="Start date filter"),
    date_to: Optional[datetime] = Query(default=None, description="End date filter"),
) -> AuditLogList:
    """Get paginated audit logs for the current user.

    Returns:
        Paginated list of audit log entries
    """
    service = AuditService(db)
    logs, total = await service.get_user_logs(
        user_id=current_user.id,
        page=page,
        limit=limit,
        action_filter=action,
        date_from=date_from,
        date_to=date_to,
    )

    total_pages = (total + limit - 1) // limit

    return AuditLogList(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.get("/export")
async def export_audit_logs(
    db: DbSession,
    current_user: CurrentUser,
    date_from: Optional[datetime] = Query(default=None, description="Start date filter"),
    date_to: Optional[datetime] = Query(default=None, description="End date filter"),
    format: str = Query(default="json", pattern="^(json|csv)$", description="Export format"),
) -> StreamingResponse:
    """Export all audit logs for the current user.

    This endpoint supports GDPR data export requirements.

    Returns:
        File download in JSON or CSV format
    """
    service = AuditService(db)
    logs = await service.export_user_logs(
        user_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
    )

    timestamp = datetime.now(UTC).replace(tzinfo=None).strftime("%Y%m%d_%H%M%S")

    if format == "csv":
        # Generate CSV
        output = io.StringIO()
        if logs:
            fieldnames = list(logs[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(logs)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{timestamp}.csv"
            },
        )
    else:
        # Generate JSON
        import json
        content = json.dumps(logs, indent=2, default=str)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{timestamp}.json"
            },
        )


@router.get("/summary", response_model=AuditActivitySummary)
async def get_activity_summary(
    db: DbSession,
    current_user: CurrentUser,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
) -> AuditActivitySummary:
    """Get activity summary for the current user.

    Returns:
        Summary of user activity by action type
    """
    service = AuditService(db)
    summary = await service.get_activity_summary(
        user_id=current_user.id,
        days=days,
    )
    return AuditActivitySummary(**summary)


@router.get("/recent", response_model=list[AuditLogResponse])
async def get_recent_activity(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=10, ge=1, le=50, description="Number of entries"),
) -> list[AuditLogResponse]:
    """Get recent activity for the current user.

    Returns:
        List of recent audit log entries
    """
    service = AuditService(db)
    logs = await service.get_recent_activity(
        user_id=current_user.id,
        limit=limit,
    )
    return [AuditLogResponse.model_validate(log) for log in logs]
