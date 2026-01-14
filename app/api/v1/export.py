"""CSV export endpoints for DATEV and Excel compatibility."""

import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, DbSession
from app.models.user import PlanType
from app.schemas.export import ExportFormat, ValidationStatus
from app.services.export import ExportService

logger = logging.getLogger(__name__)

router = APIRouter()


def _check_export_access(user) -> None:
    """Check if user can access export features."""
    if user.plan != PlanType.STEUERBERATER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSV-Export erfordert Steuerberater-Plan.",
        )


@router.get(
    "/validations",
    summary="Export validations as CSV",
    description="Download validation history as CSV file. Supports DATEV and Excel formats.",
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "CSV file with validation data",
        }
    },
)
async def export_validations(
    current_user: CurrentUser,
    db: DbSession,
    client_id: UUID | None = Query(default=None, description="Filter by client ID"),
    date_from: date | None = Query(default=None, description="Start date (inclusive)"),
    date_to: date | None = Query(default=None, description="End date (inclusive)"),
    status: ValidationStatus = Query(default=ValidationStatus.ALL, description="Filter by status"),
    format: ExportFormat = Query(default=ExportFormat.CSV_DATEV, description="Export format"),
) -> StreamingResponse:
    """Export validation history as CSV file.

    Args:
        client_id: Optional filter by client
        date_from: Optional start date filter
        date_to: Optional end date filter
        status: Filter by validation status (all, valid, invalid)
        format: Export format (datev or excel)

    Returns:
        CSV file download
    """
    _check_export_access(current_user)

    service = ExportService(db)
    csv_content = await service.export_validations(
        user_id=current_user.id,
        client_id=client_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
        format=format,
    )

    # Generate filename with date
    today = date.today().strftime("%Y%m%d")
    filename = f"validierungen_{today}.csv"

    logger.info(
        f"Validations exported: user={current_user.email}, "
        f"format={format.value}, client_id={client_id}"
    )

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


@router.get(
    "/clients",
    summary="Export clients as CSV",
    description="Download client list with validation statistics as CSV file.",
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "CSV file with client data",
        }
    },
)
async def export_clients(
    current_user: CurrentUser,
    db: DbSession,
    include_inactive: bool = Query(default=False, description="Include inactive clients"),
    date_from: date | None = Query(default=None, description="Filter validation stats from date"),
    date_to: date | None = Query(default=None, description="Filter validation stats to date"),
    format: ExportFormat = Query(default=ExportFormat.CSV_DATEV, description="Export format"),
) -> StreamingResponse:
    """Export client list with validation statistics as CSV file.

    Args:
        include_inactive: Include inactive clients in export
        date_from: Optional date filter for validation statistics
        date_to: Optional date filter for validation statistics
        format: Export format (datev or excel)

    Returns:
        CSV file download
    """
    _check_export_access(current_user)

    service = ExportService(db)
    csv_content = await service.export_clients(
        user_id=current_user.id,
        include_inactive=include_inactive,
        date_from=date_from,
        date_to=date_to,
        format=format,
    )

    # Generate filename with date
    today = date.today().strftime("%Y%m%d")
    filename = f"mandanten_{today}.csv"

    logger.info(
        f"Clients exported: user={current_user.email}, "
        f"format={format.value}, include_inactive={include_inactive}"
    )

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )
