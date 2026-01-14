"""Third-party integration endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models.integration import IntegrationType
from app.schemas.integration import (
    IntegrationCreate,
    IntegrationList,
    IntegrationResponse,
    IntegrationTestResponse,
    IntegrationUpdate,
    LexofficeFetchRequest,
    LexofficeFetchResult,
    LexofficeInvoiceList,
)
from app.services.integrations.lexoffice import lexoffice_service
from app.services.integrations.notifications import notification_service
from app.services.integrations.service import IntegrationService

logger = logging.getLogger(__name__)

router = APIRouter()


def _check_integration_access(user) -> None:
    """Check if user can access integrations."""
    if not user.can_use_integrations():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Integrationen erfordern Pro- oder Steuerberater-Plan.",
        )


# --- General Integration CRUD ---


@router.get(
    "/",
    response_model=IntegrationList,
    summary="List integrations",
    description="Get all configured integrations for the current user.",
)
async def list_integrations(
    current_user: CurrentUser,
    db: DbSession,
) -> IntegrationList:
    """List all integrations for the current user."""
    _check_integration_access(current_user)

    service = IntegrationService(db)
    integrations = await service.list_integrations(current_user.id)

    return IntegrationList(
        items=[
            IntegrationResponse(
                id=i.id,
                integration_type=i.integration_type,
                is_enabled=i.is_enabled,
                notify_on_valid=i.notify_on_valid,
                notify_on_invalid=i.notify_on_invalid,
                notify_on_warning=i.notify_on_warning,
                last_used_at=i.last_used_at,
                total_requests=i.total_requests,
                successful_requests=i.successful_requests,
                failed_requests=i.failed_requests,
                created_at=i.created_at,
                updated_at=i.updated_at,
                config_hint=service.get_config_hint(i),
            )
            for i in integrations
        ]
    )


@router.post(
    "/{integration_type}",
    response_model=IntegrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create/update integration",
    description="Create or update an integration configuration.",
)
async def create_integration(
    integration_type: IntegrationType,
    data: IntegrationCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> IntegrationResponse:
    """Create or update an integration."""
    _check_integration_access(current_user)

    # Validate config based on type
    if integration_type == IntegrationType.LEXOFFICE:
        if "api_key" not in data.config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="api_key ist erforderlich fuer Lexoffice-Integration.",
            )
        # Test connection
        valid = await lexoffice_service.test_connection(data.config["api_key"])
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungueltiger Lexoffice API-Schluessel oder Verbindungsfehler.",
            )
    else:  # Slack or Teams
        if "webhook_url" not in data.config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="webhook_url ist erforderlich.",
            )
        # Test webhook
        valid = await notification_service.test_webhook(
            data.config["webhook_url"],
            integration_type,
        )
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook-URL nicht erreichbar oder ungueltig.",
            )

    service = IntegrationService(db)
    integration = await service.create_or_update_integration(
        user_id=current_user.id,
        integration_type=integration_type,
        config=data.config,
        notify_on_valid=data.notify_on_valid,
        notify_on_invalid=data.notify_on_invalid,
        notify_on_warning=data.notify_on_warning,
    )
    await db.commit()
    await db.refresh(integration)

    logger.info(
        f"Integration configured: user={current_user.email}, "
        f"type={integration_type.value}"
    )

    return IntegrationResponse(
        id=integration.id,
        integration_type=integration.integration_type,
        is_enabled=integration.is_enabled,
        notify_on_valid=integration.notify_on_valid,
        notify_on_invalid=integration.notify_on_invalid,
        notify_on_warning=integration.notify_on_warning,
        last_used_at=integration.last_used_at,
        total_requests=integration.total_requests,
        successful_requests=integration.successful_requests,
        failed_requests=integration.failed_requests,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
        config_hint=service.get_config_hint(integration),
    )


@router.patch(
    "/{integration_type}",
    response_model=IntegrationResponse,
    summary="Update integration settings",
    description="Update integration settings (enable/disable, notification preferences).",
)
async def update_integration(
    integration_type: IntegrationType,
    data: IntegrationUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> IntegrationResponse:
    """Update integration settings."""
    _check_integration_access(current_user)

    service = IntegrationService(db)
    integration = await service.get_integration(current_user.id, integration_type)

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration nicht gefunden.",
        )

    if data.is_enabled is not None:
        integration.is_enabled = data.is_enabled
    if data.notify_on_valid is not None:
        integration.notify_on_valid = data.notify_on_valid
    if data.notify_on_invalid is not None:
        integration.notify_on_invalid = data.notify_on_invalid
    if data.notify_on_warning is not None:
        integration.notify_on_warning = data.notify_on_warning

    await db.commit()
    await db.refresh(integration)

    logger.info(
        f"Integration updated: user={current_user.email}, "
        f"type={integration_type.value}"
    )

    return IntegrationResponse(
        id=integration.id,
        integration_type=integration.integration_type,
        is_enabled=integration.is_enabled,
        notify_on_valid=integration.notify_on_valid,
        notify_on_invalid=integration.notify_on_invalid,
        notify_on_warning=integration.notify_on_warning,
        last_used_at=integration.last_used_at,
        total_requests=integration.total_requests,
        successful_requests=integration.successful_requests,
        failed_requests=integration.failed_requests,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
        config_hint=service.get_config_hint(integration),
    )


@router.delete(
    "/{integration_type}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete integration",
    description="Permanently delete an integration configuration.",
)
async def delete_integration(
    integration_type: IntegrationType,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete an integration."""
    _check_integration_access(current_user)

    service = IntegrationService(db)
    deleted = await service.delete_integration(current_user.id, integration_type)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration nicht gefunden.",
        )

    await db.commit()

    logger.info(
        f"Integration deleted: user={current_user.email}, "
        f"type={integration_type.value}"
    )


@router.post(
    "/{integration_type}/test",
    response_model=IntegrationTestResponse,
    summary="Test integration",
    description="Test an integration by sending a test request.",
)
async def test_integration(
    integration_type: IntegrationType,
    current_user: CurrentUser,
    db: DbSession,
) -> IntegrationTestResponse:
    """Test an integration."""
    _check_integration_access(current_user)

    service = IntegrationService(db)
    integration = await service.get_integration(current_user.id, integration_type)

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration nicht gefunden.",
        )

    import json
    from app.core.encryption import encryption_service

    config = json.loads(encryption_service.decrypt(integration.encrypted_config))

    if integration_type == IntegrationType.LEXOFFICE:
        success = await lexoffice_service.test_connection(config["api_key"])
        message = (
            "Lexoffice-Verbindung erfolgreich."
            if success
            else "Lexoffice-Verbindung fehlgeschlagen."
        )
    else:
        success = await notification_service.test_webhook(
            config["webhook_url"],
            integration_type,
        )
        message = (
            "Testbenachrichtigung gesendet."
            if success
            else "Webhook nicht erreichbar."
        )

    logger.info(
        f"Integration test: user={current_user.email}, "
        f"type={integration_type.value}, success={success}"
    )

    return IntegrationTestResponse(success=success, message=message)


# --- Lexoffice-specific endpoints ---


@router.get(
    "/lexoffice/invoices",
    response_model=LexofficeInvoiceList,
    summary="List Lexoffice invoices",
    description="Fetch invoices from connected Lexoffice account.",
)
async def list_lexoffice_invoices(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(default=0, ge=0, description="Page number (0-based)"),
    size: int = Query(default=25, ge=1, le=100, description="Page size"),
) -> LexofficeInvoiceList:
    """List invoices from Lexoffice."""
    _check_integration_access(current_user)

    try:
        service = lexoffice_service.with_db(db)
        return await service.list_invoices(
            user_id=current_user.id,
            page=page,
            size=size,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Lexoffice API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Fehler bei der Kommunikation mit Lexoffice.",
        )


@router.post(
    "/lexoffice/validate",
    response_model=list[LexofficeFetchResult],
    summary="Validate Lexoffice invoices",
    description="Fetch invoices from Lexoffice and validate them.",
)
async def validate_lexoffice_invoices(
    data: LexofficeFetchRequest,
    current_user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> list[LexofficeFetchResult]:
    """Fetch invoices from Lexoffice and validate them.

    Note: This endpoint fetches invoice PDFs from Lexoffice. Full XRechnung
    XML validation requires invoices to be XRechnung-compatible in Lexoffice.
    """
    _check_integration_access(current_user)

    service = lexoffice_service.with_db(db)
    results = []

    for invoice_id in data.invoice_ids:
        try:
            # Get invoice metadata
            invoice_data = await service.get_invoice(current_user.id, invoice_id)
            voucher_number = invoice_data.get("voucherNumber")

            # For now, just record that we fetched the invoice
            # Full validation would require XRechnung XML export from Lexoffice
            results.append(
                LexofficeFetchResult(
                    invoice_id=invoice_id,
                    voucher_number=voucher_number,
                    validation_id=None,
                    is_valid=None,
                    error_count=0,
                    warning_count=0,
                    error_message="Lexoffice-Validierung erfordert XRechnung-Export. "
                    "Bitte laden Sie die Rechnung als XML hoch.",
                )
            )

        except Exception as e:
            logger.error(f"Failed to fetch Lexoffice invoice {invoice_id}: {e}")
            results.append(
                LexofficeFetchResult(
                    invoice_id=invoice_id,
                    voucher_number=None,
                    validation_id=None,
                    is_valid=None,
                    error_message=str(e),
                )
            )

    return results


# --- Background notification helper ---


async def send_notifications_background(
    user_id: UUID,
    validation_id: UUID,
    file_name: str,
    is_valid: bool,
    error_count: int,
    warning_count: int,
    info_count: int,
) -> None:
    """Background task to send Slack/Teams notifications.

    Args:
        user_id: User ID
        validation_id: Validation ID
        file_name: Name of validated file
        is_valid: Whether validation passed
        error_count: Number of errors
        warning_count: Number of warnings
        info_count: Number of info messages
    """
    from app.core.database import async_session_maker

    async with async_session_maker() as db:
        try:
            service = notification_service.with_db(db)
            await service.send_validation_notification(
                user_id=user_id,
                validation_id=validation_id,
                file_name=file_name,
                is_valid=is_valid,
                error_count=error_count,
                warning_count=warning_count,
                info_count=info_count,
            )
            await db.commit()
        except Exception as e:
            logger.exception(f"Notification error: {e}")
            await db.rollback()
