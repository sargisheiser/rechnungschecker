"""Reports API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.api.deps import DbSession, OptionalUser
from app.services.reports.pdf import ReportService
from app.services.validation_history import ValidationHistoryService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{report_id}",
    summary="Get validation report",
    description="Retrieve validation report details by ID.",
    responses={
        200: {"description": "Report details"},
        404: {"description": "Report not found"},
    },
)
async def get_report(
    report_id: UUID,
    db: DbSession,
    current_user: OptionalUser,
) -> dict:
    """Get validation report details.

    Note: Full report retrieval requires storing validation results,
    which is implemented for authenticated users in the history service.
    For now, this returns a placeholder for the report endpoint.
    """
    # For MVP, we generate reports on-demand rather than storing them
    # In production, we would retrieve from database or cache
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Bericht nicht gefunden. Berichte werden direkt nach der Validierung generiert.",
    )


@router.get(
    "/{report_id}/pdf",
    summary="Download PDF report",
    description="Download the validation report as PDF.",
    responses={
        200: {
            "description": "PDF report file",
            "content": {"application/pdf": {}},
        },
        404: {"description": "Report not found"},
    },
)
async def download_report_pdf(
    report_id: UUID,
    db: DbSession,
    current_user: OptionalUser,
) -> Response:
    """Download validation report as PDF.

    Note: For MVP, reports need to be generated immediately after validation.
    This endpoint serves as a placeholder for when we implement report caching.
    """
    # Check if user has access to this report
    history_service = ValidationHistoryService(db)

    user_id = current_user.id if current_user else None
    validation_log = await history_service.get_validation_by_id(report_id, user_id)

    if validation_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bericht nicht gefunden oder kein Zugriff.",
        )

    # For MVP, we cannot regenerate the full report from just the log
    # In production, we would either:
    # 1. Cache the full validation result temporarily
    # 2. Store enough data to regenerate the report
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Bericht abgelaufen. Bitte führen Sie die Validierung erneut durch.",
    )


# Helper function to generate PDF response (used by validation endpoints)
def create_pdf_response(pdf_bytes: bytes, filename: str = "validierungsbericht.pdf") -> Response:
    """Create a FastAPI Response for PDF download.

    Args:
        pdf_bytes: PDF file content
        filename: Download filename

    Returns:
        FastAPI Response with PDF content
    """
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
