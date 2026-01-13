"""Webhook management endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func

from app.api.deps import CurrentUser, DbSession
from app.models.webhook import WebhookSubscription, WebhookDelivery, DeliveryStatus, generate_webhook_secret
from app.schemas.webhook import (
    WebhookCreate,
    WebhookCreated,
    WebhookList,
    WebhookResponse,
    WebhookUpdate,
    WebhookWithDeliveries,
    WebhookDeliveryResponse,
    WebhookTestResponse,
    DeliveryStatus as DeliveryStatusSchema,
)
from app.services.webhook import WebhookService

logger = logging.getLogger(__name__)

router = APIRouter()


def _check_webhook_access(user) -> None:
    """Check if user can access webhooks."""
    if not user.can_use_webhooks():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook-Zugang erfordert Pro- oder Steuerberater-Plan.",
        )


@router.get(
    "/",
    response_model=WebhookList,
    summary="List webhooks",
    description="Get all webhook subscriptions for the current user.",
)
async def list_webhooks(
    current_user: CurrentUser,
    db: DbSession,
) -> WebhookList:
    """List all webhooks for the current user."""
    _check_webhook_access(current_user)

    # Get all webhooks for user
    result = await db.execute(
        select(WebhookSubscription)
        .where(WebhookSubscription.user_id == current_user.id)
        .order_by(WebhookSubscription.created_at.desc())
    )
    webhooks = result.scalars().all()

    return WebhookList(
        items=[
            WebhookResponse(
                id=w.id,
                url=w.url,
                events=w.events,
                description=w.description,
                is_active=w.is_active,
                total_deliveries=w.total_deliveries,
                successful_deliveries=w.successful_deliveries,
                failed_deliveries=w.failed_deliveries,
                last_triggered_at=w.last_triggered_at,
                last_success_at=w.last_success_at,
                created_at=w.created_at,
                updated_at=w.updated_at,
            )
            for w in webhooks
        ],
        total=len(webhooks),
        max_webhooks=current_user.get_max_webhooks(),
    )


@router.post(
    "/",
    response_model=WebhookCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create webhook",
    description="Register a new webhook subscription. The secret is only shown once!",
)
async def create_webhook(
    data: WebhookCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> WebhookCreated:
    """Create a new webhook subscription."""
    _check_webhook_access(current_user)

    # Check webhook limit
    result = await db.execute(
        select(func.count(WebhookSubscription.id))
        .where(WebhookSubscription.user_id == current_user.id)
    )
    current_count = result.scalar() or 0
    max_webhooks = current_user.get_max_webhooks()

    if current_count >= max_webhooks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximale Anzahl von {max_webhooks} Webhooks erreicht.",
        )

    # Create webhook
    events = [e.value for e in data.events]
    webhook, secret = WebhookSubscription.create(
        user_id=current_user.id,
        url=str(data.url),
        events=events,
        description=data.description,
    )

    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    logger.info(f"Webhook created: user={current_user.email}, webhook_id={webhook.id}")

    return WebhookCreated(
        id=webhook.id,
        url=webhook.url,
        events=webhook.events,
        description=webhook.description,
        is_active=webhook.is_active,
        total_deliveries=webhook.total_deliveries,
        successful_deliveries=webhook.successful_deliveries,
        failed_deliveries=webhook.failed_deliveries,
        last_triggered_at=webhook.last_triggered_at,
        last_success_at=webhook.last_success_at,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
        secret=secret,
    )


@router.get(
    "/{webhook_id}",
    response_model=WebhookWithDeliveries,
    summary="Get webhook details",
    description="Get webhook details including recent delivery history.",
)
async def get_webhook(
    webhook_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> WebhookWithDeliveries:
    """Get webhook details with recent deliveries."""
    _check_webhook_access(current_user)

    # Get webhook
    result = await db.execute(
        select(WebhookSubscription)
        .where(
            WebhookSubscription.id == webhook_id,
            WebhookSubscription.user_id == current_user.id,
        )
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook nicht gefunden.",
        )

    # Get recent deliveries
    deliveries_result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.subscription_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(20)
    )
    deliveries = deliveries_result.scalars().all()

    return WebhookWithDeliveries(
        id=webhook.id,
        url=webhook.url,
        events=webhook.events,
        description=webhook.description,
        is_active=webhook.is_active,
        total_deliveries=webhook.total_deliveries,
        successful_deliveries=webhook.successful_deliveries,
        failed_deliveries=webhook.failed_deliveries,
        last_triggered_at=webhook.last_triggered_at,
        last_success_at=webhook.last_success_at,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
        recent_deliveries=[
            WebhookDeliveryResponse(
                id=d.id,
                event_type=d.event_type,
                event_id=d.event_id,
                status=DeliveryStatusSchema(d.status),
                attempt_count=d.attempt_count,
                response_status_code=d.response_status_code,
                response_time_ms=d.response_time_ms,
                error_message=d.error_message,
                created_at=d.created_at,
                last_attempt_at=d.last_attempt_at,
                completed_at=d.completed_at,
            )
            for d in deliveries
        ],
    )


@router.patch(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Update webhook",
    description="Update a webhook's URL, events, or status.",
)
async def update_webhook(
    webhook_id: UUID,
    data: WebhookUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> WebhookResponse:
    """Update a webhook subscription."""
    _check_webhook_access(current_user)

    # Get webhook
    result = await db.execute(
        select(WebhookSubscription)
        .where(
            WebhookSubscription.id == webhook_id,
            WebhookSubscription.user_id == current_user.id,
        )
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook nicht gefunden.",
        )

    # Update fields
    if data.url is not None:
        webhook.url = str(data.url)
    if data.events is not None:
        webhook.events = [e.value for e in data.events]
    if data.description is not None:
        webhook.description = data.description
    if data.is_active is not None:
        webhook.is_active = data.is_active

    await db.commit()
    await db.refresh(webhook)

    logger.info(f"Webhook updated: user={current_user.email}, webhook_id={webhook.id}")

    return WebhookResponse(
        id=webhook.id,
        url=webhook.url,
        events=webhook.events,
        description=webhook.description,
        is_active=webhook.is_active,
        total_deliveries=webhook.total_deliveries,
        successful_deliveries=webhook.successful_deliveries,
        failed_deliveries=webhook.failed_deliveries,
        last_triggered_at=webhook.last_triggered_at,
        last_success_at=webhook.last_success_at,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
    )


@router.delete(
    "/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete webhook",
    description="Permanently delete a webhook subscription.",
)
async def delete_webhook(
    webhook_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a webhook subscription."""
    _check_webhook_access(current_user)

    # Get webhook
    result = await db.execute(
        select(WebhookSubscription)
        .where(
            WebhookSubscription.id == webhook_id,
            WebhookSubscription.user_id == current_user.id,
        )
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook nicht gefunden.",
        )

    await db.delete(webhook)
    await db.commit()

    logger.info(f"Webhook deleted: user={current_user.email}, webhook_id={webhook_id}")


@router.post(
    "/{webhook_id}/test",
    response_model=WebhookTestResponse,
    summary="Test webhook",
    description="Send a test event to verify webhook configuration.",
)
async def test_webhook(
    webhook_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> WebhookTestResponse:
    """Send a test event to a webhook."""
    _check_webhook_access(current_user)

    # Verify ownership
    result = await db.execute(
        select(WebhookSubscription)
        .where(
            WebhookSubscription.id == webhook_id,
            WebhookSubscription.user_id == current_user.id,
        )
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook nicht gefunden.",
        )

    if not webhook.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook ist deaktiviert. Bitte aktivieren Sie ihn zuerst.",
        )

    # Send test event
    service = WebhookService(db)
    try:
        delivery = await service.send_test_event(webhook_id, current_user.id)
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    success = delivery.status == DeliveryStatus.SUCCESS.value
    message = (
        "Test-Event erfolgreich zugestellt."
        if success
        else f"Zustellung fehlgeschlagen: {delivery.error_message}"
    )

    logger.info(
        f"Webhook test: user={current_user.email}, webhook_id={webhook_id}, "
        f"success={success}"
    )

    return WebhookTestResponse(
        success=success,
        delivery_id=delivery.id,
        message=message,
        response_status_code=delivery.response_status_code,
        response_time_ms=delivery.response_time_ms,
    )


@router.post(
    "/{webhook_id}/rotate-secret",
    response_model=WebhookCreated,
    summary="Rotate webhook secret",
    description="Generate a new signing secret for a webhook.",
)
async def rotate_webhook_secret(
    webhook_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> WebhookCreated:
    """Rotate the signing secret for a webhook."""
    _check_webhook_access(current_user)

    # Get webhook
    result = await db.execute(
        select(WebhookSubscription)
        .where(
            WebhookSubscription.id == webhook_id,
            WebhookSubscription.user_id == current_user.id,
        )
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook nicht gefunden.",
        )

    # Generate new secret
    new_secret = generate_webhook_secret()
    webhook.secret = new_secret

    await db.commit()
    await db.refresh(webhook)

    logger.info(
        f"Webhook secret rotated: user={current_user.email}, webhook_id={webhook_id}"
    )

    return WebhookCreated(
        id=webhook.id,
        url=webhook.url,
        events=webhook.events,
        description=webhook.description,
        is_active=webhook.is_active,
        total_deliveries=webhook.total_deliveries,
        successful_deliveries=webhook.successful_deliveries,
        failed_deliveries=webhook.failed_deliveries,
        last_triggered_at=webhook.last_triggered_at,
        last_success_at=webhook.last_success_at,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
        secret=new_secret,
    )
