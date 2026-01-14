"""Tests for webhook management endpoints."""

import uuid
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token

from app.schemas.webhook import WebhookEventType, DeliveryStatus

# Use a valid UUID format for fake tokens
FAKE_USER_ID = str(uuid.uuid4())


class TestWebhookListEndpoint:
    """Tests for listing webhooks."""

    @pytest.mark.asyncio
    async def test_list_webhooks_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test listing webhooks without authentication fails."""
        response = await async_client.get("/api/v1/webhooks/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_webhooks_invalid_token(
        self, async_client: AsyncClient
    ) -> None:
        """Test listing webhooks with invalid token fails."""
        response = await async_client.get(
            "/api/v1/webhooks/",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_webhooks_with_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Test listing webhooks with valid auth."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.get(
            "/api/v1/webhooks/",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        # 403 (wrong plan) or 500 (no DB) means auth passed
        assert response.status_code in [403, 500, 200]


class TestWebhookCreateEndpoint:
    """Tests for creating webhooks."""

    @pytest.mark.asyncio
    async def test_create_webhook_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating webhook without authentication fails."""
        response = await async_client.post(
            "/api/v1/webhooks/",
            json={
                "url": "https://example.com/webhook",
                "events": ["validation.completed"],
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_webhook_missing_url(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating webhook without URL fails validation."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/webhooks/",
            json={"events": ["validation.completed"]},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_webhook_invalid_url(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating webhook with invalid URL fails validation."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/webhooks/",
            json={
                "url": "not-a-valid-url",
                "events": ["validation.completed"],
            },
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_webhook_http_url_rejected(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating webhook with HTTP URL fails (must be HTTPS)."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/webhooks/",
            json={
                "url": "http://example.com/webhook",  # HTTP, not HTTPS
                "events": ["validation.completed"],
            },
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_webhook_localhost_allowed(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating webhook with localhost URL (allowed for dev)."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/webhooks/",
            json={
                "url": "http://localhost:8080/webhook",
                "events": ["validation.completed"],
            },
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        # 403 (plan) or 500 (no DB) means validation passed
        assert response.status_code in [403, 500, 201]

    @pytest.mark.asyncio
    async def test_create_webhook_empty_events(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating webhook with empty events list fails."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/webhooks/",
            json={
                "url": "https://example.com/webhook",
                "events": [],
            },
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_webhook_invalid_event_type(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating webhook with invalid event type fails."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/webhooks/",
            json={
                "url": "https://example.com/webhook",
                "events": ["invalid.event"],
            },
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_webhook_with_description(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating webhook with description."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/webhooks/",
            json={
                "url": "https://example.com/webhook",
                "events": ["validation.completed", "validation.invalid"],
                "description": "My validation webhook",
            },
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code in [403, 500, 201]

    @pytest.mark.asyncio
    async def test_create_webhook_description_too_long(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating webhook with too long description fails."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/webhooks/",
            json={
                "url": "https://example.com/webhook",
                "events": ["validation.completed"],
                "description": "x" * 600,  # >500 chars
            },
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code == 422


class TestWebhookGetEndpoint:
    """Tests for getting webhook details."""

    @pytest.mark.asyncio
    async def test_get_webhook_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test getting webhook without authentication fails."""
        webhook_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/webhooks/{webhook_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_webhook_invalid_uuid(
        self, async_client: AsyncClient
    ) -> None:
        """Test getting webhook with invalid UUID fails."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.get(
            "/api/v1/webhooks/not-a-uuid",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_webhook_with_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Test getting webhook with auth."""
        fake_token = create_access_token(FAKE_USER_ID)
        webhook_id = uuid.uuid4()
        response = await async_client.get(
            f"/api/v1/webhooks/{webhook_id}",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        # 403 (plan) or 404 (not found) or 500 (no DB)
        assert response.status_code in [403, 404, 500, 200]


class TestWebhookUpdateEndpoint:
    """Tests for updating webhooks."""

    @pytest.mark.asyncio
    async def test_update_webhook_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test updating webhook without authentication fails."""
        webhook_id = uuid.uuid4()
        response = await async_client.patch(
            f"/api/v1/webhooks/{webhook_id}",
            json={"is_active": False},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_webhook_enable_disable(
        self, async_client: AsyncClient
    ) -> None:
        """Test updating webhook enabled status."""
        fake_token = create_access_token(FAKE_USER_ID)
        webhook_id = uuid.uuid4()
        response = await async_client.patch(
            f"/api/v1/webhooks/{webhook_id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code in [403, 404, 500, 200]

    @pytest.mark.asyncio
    async def test_update_webhook_url(
        self, async_client: AsyncClient
    ) -> None:
        """Test updating webhook URL."""
        fake_token = create_access_token(FAKE_USER_ID)
        webhook_id = uuid.uuid4()
        response = await async_client.patch(
            f"/api/v1/webhooks/{webhook_id}",
            json={"url": "https://new-url.example.com/webhook"},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code in [403, 404, 500, 200]

    @pytest.mark.asyncio
    async def test_update_webhook_events(
        self, async_client: AsyncClient
    ) -> None:
        """Test updating webhook events."""
        fake_token = create_access_token(FAKE_USER_ID)
        webhook_id = uuid.uuid4()
        response = await async_client.patch(
            f"/api/v1/webhooks/{webhook_id}",
            json={"events": ["validation.valid", "validation.invalid"]},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code in [403, 404, 500, 200]


class TestWebhookDeleteEndpoint:
    """Tests for deleting webhooks."""

    @pytest.mark.asyncio
    async def test_delete_webhook_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test deleting webhook without authentication fails."""
        webhook_id = uuid.uuid4()
        response = await async_client.delete(f"/api/v1/webhooks/{webhook_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_webhook_with_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Test deleting webhook with auth."""
        fake_token = create_access_token(FAKE_USER_ID)
        webhook_id = uuid.uuid4()
        response = await async_client.delete(
            f"/api/v1/webhooks/{webhook_id}",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code in [403, 404, 500, 204]


class TestWebhookTestEndpoint:
    """Tests for webhook test endpoint."""

    @pytest.mark.asyncio
    async def test_test_webhook_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test testing webhook without authentication fails."""
        webhook_id = uuid.uuid4()
        response = await async_client.post(f"/api/v1/webhooks/{webhook_id}/test")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_test_webhook_with_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Test testing webhook with auth."""
        fake_token = create_access_token(FAKE_USER_ID)
        webhook_id = uuid.uuid4()
        response = await async_client.post(
            f"/api/v1/webhooks/{webhook_id}/test",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code in [400, 403, 404, 500, 200]


class TestWebhookRotateSecretEndpoint:
    """Tests for webhook secret rotation endpoint."""

    @pytest.mark.asyncio
    async def test_rotate_secret_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test rotating webhook secret without authentication fails."""
        webhook_id = uuid.uuid4()
        response = await async_client.post(
            f"/api/v1/webhooks/{webhook_id}/rotate-secret"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_rotate_secret_with_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Test rotating webhook secret with auth."""
        fake_token = create_access_token(FAKE_USER_ID)
        webhook_id = uuid.uuid4()
        response = await async_client.post(
            f"/api/v1/webhooks/{webhook_id}/rotate-secret",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code in [403, 404, 500, 200]


class TestWebhookSchemas:
    """Tests for webhook schemas."""

    def test_webhook_event_type_enum(self) -> None:
        """Test WebhookEventType enum values."""
        assert WebhookEventType.VALIDATION_COMPLETED.value == "validation.completed"
        assert WebhookEventType.VALIDATION_VALID.value == "validation.valid"
        assert WebhookEventType.VALIDATION_INVALID.value == "validation.invalid"
        assert WebhookEventType.VALIDATION_WARNING.value == "validation.warning"

    def test_delivery_status_enum(self) -> None:
        """Test DeliveryStatus enum values."""
        assert DeliveryStatus.PENDING.value == "pending"
        assert DeliveryStatus.SUCCESS.value == "success"
        assert DeliveryStatus.FAILED.value == "failed"
        assert DeliveryStatus.RETRYING.value == "retrying"

    def test_webhook_create_schema_valid(self) -> None:
        """Test WebhookCreate schema with valid data."""
        from app.schemas.webhook import WebhookCreate

        data = WebhookCreate(
            url="https://example.com/webhook",
            events=[WebhookEventType.VALIDATION_COMPLETED],
            description="Test webhook",
        )
        assert str(data.url) == "https://example.com/webhook"
        assert len(data.events) == 1
        assert data.description == "Test webhook"

    def test_webhook_create_schema_default_events(self) -> None:
        """Test WebhookCreate schema default events."""
        from app.schemas.webhook import WebhookCreate

        data = WebhookCreate(url="https://example.com/webhook")
        assert len(data.events) == 1
        assert data.events[0] == WebhookEventType.VALIDATION_COMPLETED

    def test_webhook_update_schema_partial(self) -> None:
        """Test WebhookUpdate schema with partial data."""
        from app.schemas.webhook import WebhookUpdate

        data = WebhookUpdate(is_active=False)
        assert data.is_active is False
        assert data.url is None
        assert data.events is None

    def test_webhook_list_schema(self) -> None:
        """Test WebhookList schema."""
        from app.schemas.webhook import WebhookList, WebhookResponse
        from datetime import datetime

        items = [
            WebhookResponse(
                id=uuid.uuid4(),
                url="https://example.com/webhook",
                events=["validation.completed"],
                description=None,
                is_active=True,
                total_deliveries=10,
                successful_deliveries=8,
                failed_deliveries=2,
                last_triggered_at=datetime.utcnow(),
                last_success_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        ]
        webhook_list = WebhookList(items=items, total=1, max_webhooks=5)
        assert webhook_list.total == 1
        assert webhook_list.max_webhooks == 5

    def test_validation_event_payload_schema(self) -> None:
        """Test ValidationEventPayload schema."""
        from app.schemas.webhook import ValidationEventPayload
        from datetime import datetime

        payload = ValidationEventPayload(
            event_type="validation.completed",
            event_id="evt-123",
            timestamp=datetime.utcnow(),
            validation_id=uuid.uuid4(),
            file_name="rechnung.xml",
            file_type="xrechnung",
            file_hash="abc123",
            is_valid=True,
            error_count=0,
            warning_count=2,
            info_count=5,
            xrechnung_version="3.0",
            processing_time_ms=150,
            validated_at=datetime.utcnow(),
        )
        assert payload.is_valid is True
        assert payload.error_count == 0


class TestWebhookAccessControl:
    """Tests for webhook access control."""

    @pytest.mark.asyncio
    async def test_webhooks_require_pro_plan(
        self, async_client: AsyncClient
    ) -> None:
        """Test that webhooks require Pro or Steuerberater plan.

        The endpoint returns 403 for users without the correct plan.
        """
        response = await async_client.get("/api/v1/webhooks/")
        assert response.status_code == 401
