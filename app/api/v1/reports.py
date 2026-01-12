"""Reports API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.api.deps import DbSession, OptionalUser
from app.core.cache import get_cached_validation
from app.services.reports.pdf import ReportService

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
    """Get validation report details."""
    # Try to get from cache
    result = get_cached_validation(report_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bericht nicht gefunden oder abgelaufen. Bitte fuehren Sie die Validierung erneut durch.",
        )

    return {
        "id": str(result.id),
        "is_valid": result.is_valid,
        "file_type": result.file_type,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "validated_at": result.validated_at.isoformat(),
    }


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
        503: {"description": "PDF generation not available"},
    },
)
async def download_report_pdf(
    report_id: UUID,
) -> Response:
    """Download validation report as PDF."""
    # Try to get from cache
    result = get_cached_validation(report_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bericht nicht gefunden oder abgelaufen (30 Min). Bitte fuehren Sie die Validierung erneut durch.",
        )

    try:
        report_service = ReportService()
        pdf_bytes = report_service.generate_pdf(result)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="validierungsbericht-{report_id}.pdf"',
            },
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF-Generierung fehlgeschlagen: {str(e)}",
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
