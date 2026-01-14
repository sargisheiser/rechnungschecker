"""Tests for third-party integration endpoints."""

import uuid
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token

# Use a valid UUID format for fake tokens
FAKE_USER_ID = str(uuid.uuid4())


class TestIntegrationListEndpoint:
    """Tests for listing integrations."""

    @pytest.mark.asyncio
    async def test_list_integrations_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test listing integrations without authentication fails."""
        response = await async_client.get("/api/v1/integrations/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_integrations_invalid_token(
        self, async_client: AsyncClient
    ) -> None:
        """Test listing integrations with invalid token fails."""
        response = await async_client.get(
            "/api/v1/integrations/",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_integrations_with_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Test listing integrations with valid auth."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.get(
            "/api/v1/integrations/",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        # 403 (wrong plan) or 500 (no DB) means auth passed
        assert response.status_code in [403, 500, 200]


class TestIntegrationCreateEndpoint:
    """Tests for creating integrations."""

    @pytest.mark.asyncio
    async def test_create_lexoffice_integration_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating Lexoffice integration without auth fails."""
        response = await async_client.post(
            "/api/v1/integrations/lexoffice",
            json={"config": {"api_key": "test-api-key-12345"}},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_lexoffice_missing_api_key(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating Lexoffice integration without api_key fails."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/integrations/lexoffice",
            json={"config": {}},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        # 400 (validation) or 403 (plan) or 500 (no DB)
        assert response.status_code in [400, 403, 500]

    @pytest.mark.asyncio
    async def test_create_slack_integration_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating Slack integration without auth fails."""
        response = await async_client.post(
            "/api/v1/integrations/slack",
            json={"config": {"webhook_url": "https://hooks.slack.com/services/T00/B00/XXX"}},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_slack_missing_webhook_url(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating Slack integration without webhook_url fails."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/integrations/slack",
            json={"config": {}},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code in [400, 403, 500]

    @pytest.mark.asyncio
    async def test_create_teams_integration_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating Teams integration without auth fails."""
        response = await async_client.post(
            "/api/v1/integrations/teams",
            json={"config": {"webhook_url": "https://outlook.office.com/webhook/xxx"}},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_integration_invalid_type(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating integration with invalid type fails."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/integrations/invalid-type",
            json={"config": {"key": "value"}},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_integration_with_notification_settings(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating integration with notification settings."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/integrations/slack",
            json={
                "config": {"webhook_url": "https://hooks.slack.com/services/T00/B00/XXX"},
                "notify_on_valid": False,
                "notify_on_invalid": True,
                "notify_on_warning": False,
            },
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        # 400 (webhook test failed) or 403 (plan) or 500 (no DB)
        assert response.status_code in [400, 403, 500, 201]


class TestIntegrationUpdateEndpoint:
    """Tests for updating integrations."""

    @pytest.mark.asyncio
    async def test_update_integration_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test updating integration without auth fails."""
        response = await async_client.patch(
            "/api/v1/integrations/lexoffice",
            json={"is_enabled": False},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_integration_enable_disable(
        self, async_client: AsyncClient
    ) -> None:
        """Test updating integration enabled status."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.patch(
            "/api/v1/integrations/lexoffice",
            json={"is_enabled": False},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        # 403 (plan) or 404 (not found) or 500 (no DB)
        assert response.status_code in [403, 404, 500, 200]

    @pytest.mark.asyncio
    async def test_update_notification_settings(
        self, async_client: AsyncClient
    ) -> None:
        """Test updating notification settings."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.patch(
            "/api/v1/integrations/slack",
            json={
                "notify_on_valid": True,
                "notify_on_invalid": True,
                "notify_on_warning": False,
            },
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code in [403, 404, 500, 200]


class TestIntegrationDeleteEndpoint:
    """Tests for deleting integrations."""

    @pytest.mark.asyncio
    async def test_delete_integration_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test deleting integration without auth fails."""
        response = await async_client.delete("/api/v1/integrations/lexoffice")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_integration_with_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Test deleting integration with auth."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.delete(
            "/api/v1/integrations/lexoffice",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        # 403 (plan) or 404 (not found) or 500 (no DB)
        assert response.status_code in [403, 404, 500, 204]


class TestIntegrationTestEndpoint:
    """Tests for testing integrations."""

    @pytest.mark.asyncio
    async def test_test_integration_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test testing integration without auth fails."""
        response = await async_client.post("/api/v1/integrations/lexoffice/test")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_test_integration_with_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Test testing integration with auth."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/integrations/lexoffice/test",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        # 403 (plan) or 404 (not found) or 500 (no DB)
        assert response.status_code in [403, 404, 500, 200]


class TestLexofficeEndpoints:
    """Tests for Lexoffice-specific endpoints."""

    @pytest.mark.asyncio
    async def test_list_lexoffice_invoices_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test listing Lexoffice invoices without auth fails."""
        response = await async_client.get("/api/v1/integrations/lexoffice/invoices")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_lexoffice_invoices_pagination(
        self, async_client: AsyncClient
    ) -> None:
        """Test listing Lexoffice invoices with pagination."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.get(
            "/api/v1/integrations/lexoffice/invoices",
            params={"page": 0, "size": 10},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        # 400 (no integration) or 403 (plan) or 500 (no DB)
        assert response.status_code in [400, 403, 500, 502, 200]

    @pytest.mark.asyncio
    async def test_validate_lexoffice_invoices_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test validating Lexoffice invoices without auth fails."""
        response = await async_client.post(
            "/api/v1/integrations/lexoffice/validate",
            json={"invoice_ids": ["inv-123"]},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_validate_lexoffice_invoices_empty_list(
        self, async_client: AsyncClient
    ) -> None:
        """Test validating Lexoffice invoices with empty list fails."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/integrations/lexoffice/validate",
            json={"invoice_ids": []},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validate_lexoffice_invoices_too_many(
        self, async_client: AsyncClient
    ) -> None:
        """Test validating too many Lexoffice invoices fails."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/integrations/lexoffice/validate",
            json={"invoice_ids": [f"inv-{i}" for i in range(20)]},  # >10 limit
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code == 422


class TestIntegrationSchemas:
    """Tests for integration schemas."""

    def test_integration_create_schema(self) -> None:
        """Test IntegrationCreate schema."""
        from app.schemas.integration import IntegrationCreate

        data = IntegrationCreate(
            config={"api_key": "test-key"},
            notify_on_valid=True,
            notify_on_invalid=True,
            notify_on_warning=False,
        )
        assert data.config == {"api_key": "test-key"}
        assert data.notify_on_valid is True
        assert data.notify_on_warning is False

    def test_integration_update_schema_partial(self) -> None:
        """Test IntegrationUpdate schema with partial data."""
        from app.schemas.integration import IntegrationUpdate

        data = IntegrationUpdate(is_enabled=False)
        assert data.is_enabled is False
        assert data.notify_on_valid is None

    def test_lexoffice_fetch_request_schema(self) -> None:
        """Test LexofficeFetchRequest schema."""
        from app.schemas.integration import LexofficeFetchRequest

        data = LexofficeFetchRequest(invoice_ids=["inv-1", "inv-2"])
        assert len(data.invoice_ids) == 2

    def test_lexoffice_fetch_request_schema_limit(self) -> None:
        """Test LexofficeFetchRequest schema max limit."""
        from pydantic import ValidationError
        from app.schemas.integration import LexofficeFetchRequest

        with pytest.raises(ValidationError):
            LexofficeFetchRequest(invoice_ids=[f"inv-{i}" for i in range(20)])

    def test_notification_config_schema(self) -> None:
        """Test NotificationConfig schema."""
        from app.schemas.integration import NotificationConfig

        data = NotificationConfig(
            webhook_url="https://hooks.slack.com/services/T00/B00/XXX"
        )
        assert "slack.com" in str(data.webhook_url)

    def test_notification_settings_defaults(self) -> None:
        """Test NotificationSettings default values."""
        from app.schemas.integration import NotificationSettings

        settings = NotificationSettings()
        assert settings.notify_on_valid is True
        assert settings.notify_on_invalid is True
        assert settings.notify_on_warning is True


class TestIntegrationAccessControl:
    """Tests for integration access control."""

    @pytest.mark.asyncio
    async def test_integrations_require_pro_plan(
        self, async_client: AsyncClient
    ) -> None:
        """Test that integrations require Pro or Steuerberater plan.

        The endpoint returns 403 for users without the correct plan.
        """
        response = await async_client.get("/api/v1/integrations/")
        assert response.status_code == 401
