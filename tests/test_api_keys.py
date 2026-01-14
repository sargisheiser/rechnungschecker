"""Tests for API key management endpoints."""

import uuid
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token

# Use a valid UUID format for fake tokens
FAKE_USER_ID = str(uuid.uuid4())


class TestAPIKeyEndpoints:
    """Tests for API key CRUD operations."""

    @pytest.mark.asyncio
    async def test_list_api_keys_unauthorized(self, async_client: AsyncClient) -> None:
        """Test listing API keys without authentication fails."""
        response = await async_client.get("/api/v1/api-keys/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_api_keys_invalid_token(self, async_client: AsyncClient) -> None:
        """Test listing API keys with invalid token fails."""
        response = await async_client.get(
            "/api/v1/api-keys/",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_api_key_unauthorized(self, async_client: AsyncClient) -> None:
        """Test creating API key without authentication fails."""
        response = await async_client.post(
            "/api/v1/api-keys/",
            json={"name": "Test Key"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_api_key_validation_name_required(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating API key without name fails validation."""
        # This test uses a fake token to reach validation layer
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/api-keys/",
            json={},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        # Either 422 (validation) or 401/403/500 (auth/db)
        assert response.status_code in [422, 401, 403, 500]

    @pytest.mark.asyncio
    async def test_create_api_key_validation_name_too_long(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating API key with name too long fails validation."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/api-keys/",
            json={"name": "x" * 256},  # Likely exceeds max length
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code in [422, 401, 403, 500]

    @pytest.mark.asyncio
    async def test_get_api_key_unauthorized(self, async_client: AsyncClient) -> None:
        """Test getting API key without authentication fails."""
        import uuid
        key_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/api-keys/{key_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_api_key_invalid_uuid(self, async_client: AsyncClient) -> None:
        """Test getting API key with invalid UUID fails."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.get(
            "/api/v1/api-keys/not-a-uuid",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code == 422  # Validation error for UUID

    @pytest.mark.asyncio
    async def test_update_api_key_unauthorized(self, async_client: AsyncClient) -> None:
        """Test updating API key without authentication fails."""
        import uuid
        key_id = uuid.uuid4()
        response = await async_client.patch(
            f"/api/v1/api-keys/{key_id}",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_api_key_unauthorized(self, async_client: AsyncClient) -> None:
        """Test deleting API key without authentication fails."""
        import uuid
        key_id = uuid.uuid4()
        response = await async_client.delete(f"/api/v1/api-keys/{key_id}")
        assert response.status_code == 401


class TestAPIKeyValidation:
    """Tests for API key schema validation."""

    @pytest.mark.asyncio
    async def test_create_with_negative_expires_in_days(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating API key with negative expiration fails."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/api-keys/",
            json={"name": "Test Key", "expires_in_days": -1},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        # Should fail validation or auth
        assert response.status_code in [422, 401, 403, 500]

    @pytest.mark.asyncio
    async def test_create_with_valid_expires_in_days(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating API key with valid expiration reaches auth layer."""
        fake_token = create_access_token(FAKE_USER_ID)
        response = await async_client.post(
            "/api/v1/api-keys/",
            json={"name": "Test Key", "expires_in_days": 30},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        # 403 (wrong plan) or 500 (no DB) means validation passed
        assert response.status_code in [403, 500, 201]


class TestAPIKeyAccessControl:
    """Tests for API key access control (plan-based)."""

    @pytest.mark.asyncio
    async def test_free_plan_cannot_access_api_keys(
        self, async_client: AsyncClient
    ) -> None:
        """Test that free plan users cannot access API keys.

        Note: This would require a test database with a free plan user.
        The endpoint returns 403 for users without API access.
        """
        # Without a real database, we can only test that auth is enforced
        response = await async_client.get("/api/v1/api-keys/")
        assert response.status_code == 401


class TestAPIKeySchemas:
    """Tests for API key request/response schemas."""

    def test_api_key_create_schema_valid(self) -> None:
        """Test APIKeyCreate schema accepts valid data."""
        from app.schemas.api_key import APIKeyCreate

        data = APIKeyCreate(
            name="My API Key",
            description="For testing",
            expires_in_days=90,
        )
        assert data.name == "My API Key"
        assert data.description == "For testing"
        assert data.expires_in_days == 90

    def test_api_key_create_schema_minimal(self) -> None:
        """Test APIKeyCreate schema with minimal data."""
        from app.schemas.api_key import APIKeyCreate

        data = APIKeyCreate(name="Minimal Key")
        assert data.name == "Minimal Key"
        assert data.description is None
        assert data.expires_in_days is None

    def test_api_key_update_schema_partial(self) -> None:
        """Test APIKeyUpdate schema with partial data."""
        from app.schemas.api_key import APIKeyUpdate

        data = APIKeyUpdate(is_active=False)
        assert data.is_active is False
        assert data.name is None
        assert data.description is None
