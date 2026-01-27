"""Webhook delivery service."""

import hashlib
import hmac
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.webhook import (
    DeliveryStatus,
    WebhookDelivery,
    WebhookEventType,
    WebhookSubscription,
)
from app.schemas.webhook import ValidationEventPayload

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for managing and delivering webhooks."""

    DELIVERY_TIMEOUT_SECONDS = 30
    MAX_RESPONSE_BODY_SIZE = 5000

    def __init__(self, db: AsyncSession | None = None):
        """Initialize webhook service."""
        self.db = db

    def with_db(self, db: AsyncSession) -> "WebhookService":
        """Return a new instance with database session."""
        return WebhookService(db)

    # --- Signature generation ---

    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload.

        Args:
            payload: JSON payload string
            secret: Webhook signing secret

        Returns:
            Signature in format: sha256=<hex_digest>
        """
        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    @staticmethod
    def verify_signature(payload: str, secret: str, signature: str) -> bool:
        """Verify webhook signature.

        Args:
            payload: JSON payload string
            secret: Webhook signing secret
            signature: Signature to verify (sha256=<hex>)

        Returns:
            True if signature is valid
        """
        expected = WebhookService.generate_signature(payload, secret)
        return hmac.compare_digest(expected, signature)

    # --- Event determination ---

    @staticmethod
    def determine_event_types(is_valid: bool, warning_count: int) -> list[WebhookEventType]:
        """Determine which event types apply to a validation result.

        Args:
            is_valid: Whether validation passed
            warning_count: Number of warnings

        Returns:
            List of applicable event types
        """
        events = [WebhookEventType.VALIDATION_COMPLETED]

        if is_valid:
            if warning_count > 0:
                events.append(WebhookEventType.VALIDATION_WARNING)
            else:
                events.append(WebhookEventType.VALIDATION_VALID)
        else:
            events.append(WebhookEventType.VALIDATION_INVALID)

        return events

    # --- Payload building ---

    def build_payload(
        self,
        event_type: WebhookEventType,
        validation_id: UUID,
        file_name: str | None,
        file_type: str,
        file_hash: str,
        is_valid: bool,
        error_count: int,
        warning_count: int,
        info_count: int,
        processing_time_ms: int,
        validated_at: datetime,
        xrechnung_version: str | None = None,
        zugferd_profile: str | None = None,
        client_id: UUID | None = None,
        client_name: str | None = None,
    ) -> ValidationEventPayload:
        """Build webhook payload from validation data."""
        return ValidationEventPayload(
            event_type=event_type.value,
            event_id=f"evt_{uuid4().hex}",
            timestamp=datetime.now(UTC).replace(tzinfo=None),
            validation_id=validation_id,
            file_name=file_name,
            file_type=file_type,
            file_hash=file_hash,
            is_valid=is_valid,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            xrechnung_version=xrechnung_version,
            zugferd_profile=zugferd_profile,
            processing_time_ms=processing_time_ms,
            validated_at=validated_at,
            client_id=client_id,
            client_name=client_name,
        )

    # --- Webhook triggering ---

    async def trigger_webhooks(
        self,
        user_id: UUID,
        validation_id: UUID,
        file_name: str | None,
        file_type: str,
        file_hash: str,
        is_valid: bool,
        error_count: int,
        warning_count: int,
        info_count: int,
        processing_time_ms: int,
        validated_at: datetime,
        xrechnung_version: str | None = None,
        zugferd_profile: str | None = None,
        client_id: UUID | None = None,
        client_name: str | None = None,
    ) -> list[UUID]:
        """Trigger webhooks for a validation result.

        This method finds all active webhook subscriptions for the user,
        determines which events apply, creates delivery records, and
        returns delivery IDs for background processing.

        Returns:
            List of WebhookDelivery IDs to process
        """
        if self.db is None:
            raise ValueError("Database session required")

        # Get user's active webhooks
        query = select(WebhookSubscription).where(
            WebhookSubscription.user_id == user_id,
            WebhookSubscription.is_active == True,  # noqa: E712
        )
        db_result = await self.db.execute(query)
        subscriptions = db_result.scalars().all()

        if not subscriptions:
            return []

        # Determine applicable events
        event_types = self.determine_event_types(is_valid, warning_count)
        delivery_ids = []

        for subscription in subscriptions:
            # Check if subscription is interested in any of the events
            matching_events = [
                et for et in event_types
                if et.value in subscription.events
            ]

            if not matching_events:
                continue

            # Create delivery for the most specific event
            # Priority: valid/invalid/warning > completed
            event_to_send = matching_events[-1]  # Most specific is last

            # Build payload
            payload = self.build_payload(
                event_type=event_to_send,
                validation_id=validation_id,
                file_name=file_name,
                file_type=file_type,
                file_hash=file_hash,
                is_valid=is_valid,
                error_count=error_count,
                warning_count=warning_count,
                info_count=info_count,
                processing_time_ms=processing_time_ms,
                validated_at=validated_at,
                xrechnung_version=xrechnung_version,
                zugferd_profile=zugferd_profile,
                client_id=client_id,
                client_name=client_name,
            )

            # Create delivery record
            delivery = WebhookDelivery(
                subscription_id=subscription.id,
                event_type=event_to_send.value,
                event_id=payload.event_id,
                payload=payload.model_dump_json(),
                status=DeliveryStatus.PENDING.value,
            )

            self.db.add(delivery)
            await self.db.flush()

            delivery_ids.append(delivery.id)

            # Update subscription stats
            subscription.total_deliveries += 1
            subscription.last_triggered_at = datetime.now(UTC).replace(tzinfo=None)

        logger.info(
            f"Triggered {len(delivery_ids)} webhooks for user {user_id}, "
            f"validation {validation_id}"
        )

        return delivery_ids

    # --- Webhook delivery ---

    async def deliver_webhook(self, delivery_id: UUID) -> bool:
        """Deliver a single webhook.

        Args:
            delivery_id: ID of the delivery to process

        Returns:
            True if delivery succeeded
        """
        if self.db is None:
            raise ValueError("Database session required")

        # Get delivery with subscription
        query = (
            select(WebhookDelivery)
            .options(selectinload(WebhookDelivery.subscription))
            .where(WebhookDelivery.id == delivery_id)
        )
        result = await self.db.execute(query)
        delivery = result.scalar_one_or_none()

        if not delivery:
            logger.error(f"Delivery not found: {delivery_id}")
            return False

        subscription = delivery.subscription
        if not subscription or not subscription.is_active:
            logger.warning(f"Subscription inactive for delivery {delivery_id}")
            delivery.status = DeliveryStatus.FAILED.value
            delivery.error_message = "Subscription is inactive"
            delivery.completed_at = datetime.now(UTC).replace(tzinfo=None)
            return False

        # Prepare request
        payload = delivery.payload
        signature = self.generate_signature(payload, subscription.secret)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-ID": str(subscription.id),
            "X-Webhook-Event": delivery.event_type,
            "X-Webhook-Delivery": str(delivery.id),
            "X-Signature-256": signature,
            "User-Agent": "RechnungsChecker-Webhook/1.0",
        }

        # Attempt delivery
        start_time = datetime.now(UTC).replace(tzinfo=None)
        try:
            async with httpx.AsyncClient(timeout=self.DELIVERY_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    subscription.url,
                    content=payload,
                    headers=headers,
                )

            response_time_ms = int((datetime.now(UTC).replace(tzinfo=None) - start_time).total_seconds() * 1000)
            response_body = response.text[:self.MAX_RESPONSE_BODY_SIZE] if response.text else None

            # Check for success (2xx status codes)
            if 200 <= response.status_code < 300:
                delivery.mark_success(
                    status_code=response.status_code,
                    response_body=response_body,
                    response_time_ms=response_time_ms,
                )
                subscription.successful_deliveries += 1
                subscription.last_success_at = datetime.now(UTC).replace(tzinfo=None)
                logger.info(
                    f"Webhook delivered successfully: delivery={delivery_id}, "
                    f"status={response.status_code}, time={response_time_ms}ms"
                )
                return True
            else:
                delivery.mark_failed(
                    error=f"HTTP {response.status_code}: {response.reason_phrase}",
                    status_code=response.status_code,
                    response_body=response_body,
                )
                if delivery.status == DeliveryStatus.FAILED.value:
                    subscription.failed_deliveries += 1
                    subscription.last_failure_at = datetime.now(UTC).replace(tzinfo=None)
                logger.warning(
                    f"Webhook delivery failed: delivery={delivery_id}, "
                    f"status={response.status_code}, attempt={delivery.attempt_count}"
                )
                return False

        except httpx.TimeoutException:
            delivery.mark_failed(error="Request timed out")
            if delivery.status == DeliveryStatus.FAILED.value:
                subscription.failed_deliveries += 1
                subscription.last_failure_at = datetime.now(UTC).replace(tzinfo=None)
            logger.warning(f"Webhook timed out: delivery={delivery_id}")
            return False

        except httpx.RequestError as e:
            delivery.mark_failed(error=f"Request error: {str(e)}")
            if delivery.status == DeliveryStatus.FAILED.value:
                subscription.failed_deliveries += 1
                subscription.last_failure_at = datetime.now(UTC).replace(tzinfo=None)
            logger.warning(f"Webhook request error: delivery={delivery_id}, error={e}")
            return False

        except Exception as e:
            delivery.mark_failed(error=f"Unexpected error: {str(e)}")
            if delivery.status == DeliveryStatus.FAILED.value:
                subscription.failed_deliveries += 1
                subscription.last_failure_at = datetime.now(UTC).replace(tzinfo=None)
            logger.exception(f"Unexpected webhook error: delivery={delivery_id}")
            return False

    # --- Retry processing ---

    async def process_retries(self, limit: int = 100) -> int:
        """Process pending webhook retries.

        Args:
            limit: Maximum number of retries to process

        Returns:
            Number of retries processed
        """
        if self.db is None:
            raise ValueError("Database session required")

        # Find deliveries due for retry
        now = datetime.now(UTC).replace(tzinfo=None)
        query = (
            select(WebhookDelivery)
            .where(
                WebhookDelivery.status == DeliveryStatus.RETRYING.value,
                WebhookDelivery.next_retry_at <= now,
            )
            .order_by(WebhookDelivery.next_retry_at)
            .limit(limit)
        )
        result = await self.db.execute(query)
        deliveries = result.scalars().all()

        processed = 0
        for delivery in deliveries:
            await self.deliver_webhook(delivery.id)
            processed += 1

        if processed > 0:
            logger.info(f"Processed {processed} webhook retries")

        return processed

    # --- Test webhook ---

    async def send_test_event(self, subscription_id: UUID, user_id: UUID) -> WebhookDelivery:
        """Send a test event to a webhook.

        Args:
            subscription_id: Webhook subscription ID
            user_id: User ID (for authorization)

        Returns:
            WebhookDelivery record
        """
        if self.db is None:
            raise ValueError("Database session required")

        # Get subscription
        query = select(WebhookSubscription).where(
            WebhookSubscription.id == subscription_id,
            WebhookSubscription.user_id == user_id,
        )
        result = await self.db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise ValueError("Webhook subscription not found")

        # Create test payload
        test_payload = ValidationEventPayload(
            event_type="test",
            event_id=f"evt_test_{uuid4().hex}",
            timestamp=datetime.now(UTC).replace(tzinfo=None),
            validation_id=uuid4(),
            file_name="test-invoice.xml",
            file_type="xrechnung",
            file_hash="0" * 64,
            is_valid=True,
            error_count=0,
            warning_count=1,
            info_count=2,
            xrechnung_version="3.0.2",
            processing_time_ms=150,
            validated_at=datetime.now(UTC).replace(tzinfo=None),
        )

        # Create delivery record
        delivery = WebhookDelivery(
            subscription_id=subscription.id,
            event_type="test",
            event_id=test_payload.event_id,
            payload=test_payload.model_dump_json(),
            status=DeliveryStatus.PENDING.value,
            max_attempts=1,  # No retries for test events
        )

        self.db.add(delivery)
        await self.db.flush()

        # Deliver immediately
        await self.deliver_webhook(delivery.id)
        await self.db.refresh(delivery)

        return delivery


# Singleton instance (without DB session)
webhook_service = WebhookService()
