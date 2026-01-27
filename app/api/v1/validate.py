"""Validation API endpoints."""

import logging
from datetime import date
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, OptionalUser
from app.config import get_settings
from app.core.cache import cache_validation_result
from app.core.exceptions import (
    ErrorCode,
    FileProcessingError,
    KoSITError,
    ValidationError,
    api_error,
)
from app.models.user import GuestUsage, User
from app.schemas.validation import (
    GuestValidationResponse,
    UpdateNotesRequest,
    ValidationDetailResponse,
    ValidationHistoryResponse,
    ValidationResponse,
)
from app.services.validation_history import ValidationHistoryService
from app.services.validator.xrechnung import XRechnungValidator
from app.services.validator.zugferd import ZUGFeRDValidator
from app.services.webhook import WebhookService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# Guest validation limit
GUEST_VALIDATION_LIMIT = 1


async def deliver_webhook_background(delivery_id: UUID) -> None:
    """Background task to deliver a webhook."""
    from app.core.database import async_session_maker

    async with async_session_maker() as db:
        try:
            service = WebhookService(db)
            await service.deliver_webhook(delivery_id)
            await db.commit()
        except Exception as e:
            logger.exception(f"Webhook delivery failed: {delivery_id}, error: {e}")
            await db.rollback()


async def check_and_update_user_usage(user: User, db) -> None:
    """Check if user can validate and update usage counter.

    Raises HTTPException if limit exceeded.
    """
    # Reset monthly counter if needed
    today = date.today()
    if user.usage_reset_date.month != today.month or user.usage_reset_date.year != today.year:
        user.validations_this_month = 0
        user.conversions_this_month = 0
        user.usage_reset_date = today

    # Check if user can validate
    if not user.can_validate():
        limit = user.get_validation_limit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=api_error(
                ErrorCode.VALIDATION_LIMIT_REACHED,
                f"Sie haben Ihr monatliches Limit von {limit} Validierungen erreicht. "
                "Bitte upgraden Sie Ihren Plan für mehr Validierungen.",
                validations_used=user.validations_this_month,
                validations_limit=limit,
            )
        )

    # Increment validation counter
    user.validations_this_month += 1


@router.post(
    "/",
    response_model=ValidationResponse,
    summary="Validate invoice file",
    description="Upload an invoice file (XML or PDF) to validate. Auto-detects file type.",
    responses={
        200: {"description": "Validation completed (check is_valid field)"},
        400: {"description": "Invalid file format or processing error"},
        413: {"description": "File too large"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def validate_file(
    request: Request,
    db: DbSession,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="Invoice file (XML or PDF)")],
    current_user: OptionalUser,
    client_id: Annotated[UUID | None, Form(description="Optional client ID for Steuerberater")] = None,
) -> ValidationResponse:
    """Validate an invoice file with auto-detection.

    Automatically detects if the file is XRechnung (XML) or ZUGFeRD (PDF)
    and validates accordingly.
    """
    # Check usage limits for authenticated users
    if current_user:
        await check_and_update_user_usage(current_user, db)

    # Validate client_id if provided
    validated_client_id = None
    if client_id and current_user:
        if not current_user.can_manage_clients():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Mandantenverwaltung erfordert den Steuerberater-Plan.",
            )
        # Verify client belongs to user
        from app.models.client import Client
        result = await db.execute(
            select(Client).where(
                Client.id == client_id,
                Client.user_id == current_user.id,
            )
        )
        client = result.scalar_one_or_none()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mandant nicht gefunden.",
            )
        validated_client_id = client_id

    # Check file size
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Datei zu groß. Maximum: {settings.max_upload_size_mb}MB",
        )

    filename = file.filename or "unknown"
    is_pdf = filename.lower().endswith(".pdf")
    is_xml = filename.lower().endswith(".xml")

    if not is_pdf and not is_xml:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger Dateityp. Bitte laden Sie eine XML- oder PDF-Datei hoch.",
        )

    try:
        if is_pdf:
            validator = ZUGFeRDValidator()
        else:
            validator = XRechnungValidator()

        user_id = current_user.id if current_user else None

        result = await validator.validate(
            content=content,
            filename=filename,
            user_id=user_id,
        )

        # Set report URL
        result.report_url = f"/api/v1/reports/{result.id}/pdf"

        # Cache result for PDF generation
        cache_validation_result(result)

        # Store validation in history for authenticated users
        if current_user:
            history_service = ValidationHistoryService(db)
            await history_service.store_validation(
                result=result,
                user_id=current_user.id,
                client_id=validated_client_id,
                file_name=filename,
                file_size_bytes=len(content),
            )

            # Trigger webhooks for PRO+ users
            if current_user.can_use_webhooks():
                webhook_service = WebhookService(db)
                # Get client name if applicable
                client_name = client.name if validated_client_id and client else None

                delivery_ids = await webhook_service.trigger_webhooks(
                    user_id=current_user.id,
                    validation_id=result.id,
                    file_name=filename,
                    file_type=result.file_type,
                    file_hash=result.file_hash,
                    is_valid=result.is_valid,
                    error_count=result.error_count,
                    warning_count=result.warning_count,
                    info_count=result.info_count,
                    processing_time_ms=result.processing_time_ms,
                    validated_at=result.validated_at,
                    xrechnung_version=result.xrechnung_version,
                    zugferd_profile=result.zugferd_profile,
                    client_id=validated_client_id,
                    client_name=client_name,
                )

                # Schedule background delivery for each webhook
                for delivery_id in delivery_ids:
                    background_tasks.add_task(deliver_webhook_background, delivery_id)

            # Trigger Slack/Teams notifications for PRO+ users
            if current_user.can_use_integrations():
                from app.api.v1.integrations import send_notifications_background

                background_tasks.add_task(
                    send_notifications_background,
                    user_id=current_user.id,
                    validation_id=result.id,
                    file_name=filename,
                    is_valid=result.is_valid,
                    error_count=result.error_count,
                    warning_count=result.warning_count,
                    info_count=result.info_count,
                )

            await db.commit()

            # Include usage info in response
            result.validations_used = current_user.validations_this_month
            result.validations_limit = current_user.get_validation_limit()

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
    current_user: OptionalUser,
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
        user_id = current_user.id if current_user else None
        result = await validator.validate(
            content=content,
            filename=filename,
            user_id=user_id,
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
    current_user: OptionalUser,
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
        user_id = current_user.id if current_user else None
        result = await validator.validate(
            content=content,
            filename=filename,
            user_id=user_id,
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
    db: DbSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
    client_id: UUID | None = None,
) -> ValidationHistoryResponse:
    """Get validation history for the authenticated user.

    Returns a paginated list of past validations including:
    - Validation ID
    - File name
    - File type (xrechnung/zugferd)
    - Validation result (valid/invalid)
    - Error and warning counts
    - Timestamp
    """
    # Validate client_id if provided
    validated_client_id = None
    if client_id:
        if not current_user.can_manage_clients():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Mandantenverwaltung erfordert den Steuerberater-Plan.",
            )
        # Verify client belongs to user
        from app.models.client import Client
        result = await db.execute(
            select(Client).where(
                Client.id == client_id,
                Client.user_id == current_user.id,
            )
        )
        client = result.scalar_one_or_none()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mandant nicht gefunden.",
            )
        validated_client_id = client_id

    history_service = ValidationHistoryService(db)
    return await history_service.get_user_history(
        user_id=current_user.id,
        client_id=validated_client_id,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/guest",
    response_model=GuestValidationResponse,
    summary="Validate as guest (1 free validation)",
    description="Upload an invoice file to validate. Guests get 1 free validation.",
    responses={
        200: {"description": "Validation completed"},
        400: {"description": "Invalid file format"},
        403: {"description": "Guest validation limit reached - please register"},
        413: {"description": "File too large"},
    },
)
async def validate_guest(
    request: Request,
    db: DbSession,
    file: Annotated[UploadFile, File(description="Invoice file (XML or PDF)")],
    guest_id: Annotated[str | None, Form()] = None,
) -> GuestValidationResponse:
    """Validate an invoice file as a guest.

    Guests can validate 1 invoice for free. After that, they need to register.
    The guest is tracked by IP address and optional guest_id cookie.
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    # Check if guest has already used their free validation
    query = select(GuestUsage).where(GuestUsage.ip_address == client_ip)
    if guest_id:
        query = query.where(GuestUsage.cookie_id == guest_id)

    result = await db.execute(query)
    guest_usage = result.scalar_one_or_none()

    # Generate guest_id if not provided
    new_guest_id = guest_id or str(uuid4())[:16]

    if guest_usage and guest_usage.validations_used >= GUEST_VALIDATION_LIMIT:
        # Limit reached
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=api_error(
                ErrorCode.GUEST_LIMIT_REACHED,
                "Sie haben Ihre kostenlose Validierung bereits genutzt. "
                "Bitte registrieren Sie sich für weitere Validierungen.",
                guest_id=new_guest_id,
                validations_used=guest_usage.validations_used,
                validations_limit=GUEST_VALIDATION_LIMIT,
            )
        )

    # Check file size
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Datei zu groß. Maximum: {settings.max_upload_size_mb}MB",
        )

    # Detect file type and validate
    filename = file.filename or "unknown"
    is_pdf = filename.lower().endswith(".pdf")
    is_xml = filename.lower().endswith(".xml")

    if not is_pdf and not is_xml:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger Dateityp. Bitte laden Sie eine XML- oder PDF-Datei hoch.",
        )

    try:
        if is_pdf:
            validator = ZUGFeRDValidator()
        else:
            validator = XRechnungValidator()

        validation_result = await validator.validate(
            content=content,
            filename=filename,
            user_id=None,
        )

        # Track guest usage
        if guest_usage:
            guest_usage.validations_used += 1
        else:
            guest_usage = GuestUsage(
                ip_address=client_ip,
                cookie_id=new_guest_id,
                validations_used=1,
            )
            db.add(guest_usage)

        await db.flush()

        # Set report URL
        validation_result.report_url = f"/api/v1/reports/{validation_result.id}/pdf"

        # Cache result for PDF generation
        cache_validation_result(validation_result)

        logger.info(
            f"Guest validation completed: id={validation_result.id}, "
            f"valid={validation_result.is_valid}, ip={client_ip}"
        )

        # Return response with guest tracking info
        return GuestValidationResponse(
            **validation_result.model_dump(exclude={"validations_used", "validations_limit"}),
            guest_id=new_guest_id,
            validations_used=guest_usage.validations_used,
            validations_limit=GUEST_VALIDATION_LIMIT,
        )

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
        logger.exception(f"Unexpected error during guest validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ein unerwarteter Fehler ist aufgetreten.",
        )


@router.get(
    "/{validation_id}",
    response_model=ValidationDetailResponse,
    summary="Get validation details",
    description="Get detailed information about a specific validation.",
    responses={
        200: {"description": "Validation details"},
        404: {"description": "Validation not found"},
    },
)
async def get_validation_detail(
    validation_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ValidationDetailResponse:
    """Get detailed information about a specific validation.

    Returns full validation details including notes.
    Only accessible by the user who performed the validation.
    """
    from app.models.validation import ValidationLog

    result = await db.execute(
        select(ValidationLog).where(
            ValidationLog.id == validation_id,
            ValidationLog.user_id == current_user.id,
        )
    )
    validation = result.scalar_one_or_none()

    if validation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validierung nicht gefunden.",
        )

    return ValidationDetailResponse(
        id=validation.id,
        file_name=validation.file_name,
        file_type=validation.file_type.value,
        file_hash=validation.file_hash,
        is_valid=validation.is_valid,
        error_count=validation.error_count,
        warning_count=validation.warning_count,
        info_count=validation.info_count,
        xrechnung_version=validation.xrechnung_version,
        zugferd_profile=validation.zugferd_profile,
        processing_time_ms=validation.processing_time_ms,
        validator_version=validation.validator_version,
        notes=validation.notes,
        validated_at=validation.created_at,
    )


@router.patch(
    "/{validation_id}/notes",
    response_model=ValidationDetailResponse,
    summary="Update validation notes",
    description="Add or update notes for a validation.",
    responses={
        200: {"description": "Notes updated"},
        404: {"description": "Validation not found"},
    },
)
async def update_validation_notes(
    validation_id: UUID,
    request: UpdateNotesRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> ValidationDetailResponse:
    """Update notes for a specific validation.

    Only the user who performed the validation can update notes.
    """
    from app.models.validation import ValidationLog

    result = await db.execute(
        select(ValidationLog).where(
            ValidationLog.id == validation_id,
            ValidationLog.user_id == current_user.id,
        )
    )
    validation = result.scalar_one_or_none()

    if validation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validierung nicht gefunden.",
        )

    validation.notes = request.notes
    await db.commit()
    await db.refresh(validation)

    return ValidationDetailResponse(
        id=validation.id,
        file_name=validation.file_name,
        file_type=validation.file_type.value,
        file_hash=validation.file_hash,
        is_valid=validation.is_valid,
        error_count=validation.error_count,
        warning_count=validation.warning_count,
        info_count=validation.info_count,
        xrechnung_version=validation.xrechnung_version,
        zugferd_profile=validation.zugferd_profile,
        processing_time_ms=validation.processing_time_ms,
        validator_version=validation.validator_version,
        notes=validation.notes,
        validated_at=validation.created_at,
    )
