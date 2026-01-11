"""Validation API endpoints."""

import hashlib
import logging
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from app.config import get_settings
from app.core.exceptions import FileProcessingError, KoSITError, ValidationError
from app.schemas.validation import ValidationHistoryResponse, ValidationResponse
from app.services.validator.xrechnung import XRechnungValidator
from app.services.validator.zugferd import ZUGFeRDValidator

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


@router.post(
    "/xrechnung",
    response_model=ValidationResponse,
    summary="Validate XRechnung XML",
    description="Upload an XRechnung XML file to validate against official KoSIT rules.",
    responses={
        200: {"description": "Validation completed (check is_valid field)"},
        400: {"description": "Invalid file format or processing error"},
        413: {"description": "File too large"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def validate_xrechnung(
    request: Request,
    file: Annotated[UploadFile, File(description="XRechnung XML file to validate")],
) -> ValidationResponse:
    """Validate an XRechnung XML file.

    Validates the uploaded XML file against official KoSIT XRechnung rules
    and returns detailed error messages in German.

    - Accepts XRechnung 2.x and 3.x formats
    - Returns validation errors, warnings, and info messages
    - All messages include German explanations and fix suggestions
    """
    # Check file size
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Datei zu groß. Maximum: {settings.max_upload_size_mb}MB",
        )

    # Check file extension
    filename = file.filename or "unknown.xml"
    if not filename.lower().endswith(".xml"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger Dateityp. Bitte laden Sie eine XML-Datei hoch.",
        )

    # Check content type
    if file.content_type and "xml" not in file.content_type.lower():
        logger.warning(f"Unexpected content type: {file.content_type}")
        # Don't reject, just log - content type detection is unreliable

    try:
        validator = XRechnungValidator()
        result = await validator.validate(
            content=content,
            filename=filename,
            user_id=None,  # TODO: Get from auth context
        )

        # Set report URL
        result.report_url = f"/api/v1/reports/{result.id}/pdf"

        logger.info(
            f"Validation completed: id={result.id}, valid={result.is_valid}, "
            f"errors={result.error_count}, warnings={result.warning_count}"
        )

        return result

    except FileProcessingError as e:
        logger.warning(f"File processing error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except KoSITError as e:
        logger.error(f"KoSIT validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validierung fehlgeschlagen. Bitte versuchen Sie es später erneut.",
        )
    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ein unerwarteter Fehler ist aufgetreten.",
        )


@router.post(
    "/zugferd",
    response_model=ValidationResponse,
    summary="Validate ZUGFeRD PDF",
    description="Upload a ZUGFeRD PDF file to validate the embedded XML data.",
    responses={
        200: {"description": "Validation completed (check is_valid field)"},
        400: {"description": "Invalid file format or no embedded XML found"},
        413: {"description": "File too large"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def validate_zugferd(
    request: Request,
    file: Annotated[UploadFile, File(description="ZUGFeRD PDF file to validate")],
) -> ValidationResponse:
    """Validate a ZUGFeRD PDF file.

    Extracts the embedded XML from a ZUGFeRD PDF and validates it
    against official rules.

    - Supports ZUGFeRD 2.1.1 and 2.2 profiles
    - Also validates Factur-X (French equivalent)
    - Returns validation errors in German
    """
    # Check file size
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Datei zu groß. Maximum: {settings.max_upload_size_mb}MB",
        )

    # Check file extension
    filename = file.filename or "unknown.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger Dateityp. Bitte laden Sie eine PDF-Datei hoch.",
        )

    try:
        validator = ZUGFeRDValidator()
        result = await validator.validate(
            content=content,
            filename=filename,
            user_id=None,  # TODO: Get from auth context
        )

        # Set report URL
        result.report_url = f"/api/v1/reports/{result.id}/pdf"

        logger.info(
            f"ZUGFeRD validation completed: id={result.id}, valid={result.is_valid}, "
            f"profile={result.zugferd_profile}, errors={result.error_count}"
        )

        return result

    except FileProcessingError as e:
        logger.warning(f"File processing error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except KoSITError as e:
        logger.error(f"KoSIT validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validierung fehlgeschlagen. Bitte versuchen Sie es später erneut.",
        )
    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except Exception as e:
        logger.exception(f"Unexpected error during ZUGFeRD validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ein unerwarteter Fehler ist aufgetreten.",
        )


@router.get(
    "/history",
    response_model=ValidationHistoryResponse,
    summary="Get validation history",
    description="Retrieve the validation history for the authenticated user.",
    responses={
        200: {"description": "Validation history retrieved"},
        401: {"description": "Not authenticated"},
    },
)
async def get_validation_history(
    request: Request,
    page: int = 1,
    page_size: int = 20,
) -> ValidationHistoryResponse:
    """Get validation history for the authenticated user.

    Returns a paginated list of past validations including:
    - Validation ID
    - File type (xrechnung/zugferd)
    - Validation result (valid/invalid)
    - Error and warning counts
    - Timestamp
    """
    # TODO: Implement with auth - for now return empty
    # This will be fully implemented when authentication is added
    return ValidationHistoryResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
    )
