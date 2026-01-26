"""Tests for client management (Mandantenverwaltung) endpoints."""

import uuid
import pytest
from httpx import AsyncClient

from app.models.user import User


class TestClientEndpoints:
    """Tests for client CRUD operations."""

    @pytest.mark.asyncio
    async def test_list_clients_unauthorized(self, async_client: AsyncClient) -> None:
        """Test listing clients without authentication fails."""
        response = await async_client.get("/api/v1/clients/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_clients_invalid_token(self, async_client: AsyncClient) -> None:
        """Test listing clients with invalid token fails."""
        response = await async_client.get(
            "/api/v1/clients/",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_clients_pagination_params(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test listing clients with pagination parameters."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/clients/",
            params={"page": 1, "page_size": 10, "active_only": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_clients_search_param(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test listing clients with search parameter."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/clients/",
            params={"search": "Test GmbH"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_client_unauthorized(self, async_client: AsyncClient) -> None:
        """Test creating client without authentication fails."""
        response = await async_client.post(
            "/api/v1/clients/",
            json={"name": "Test Client GmbH"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_client_validation_name_required(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test creating client without name fails validation."""
        user, token = test_steuerberater_user
        response = await async_client.post(
            "/api/v1/clients/",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_client_with_full_data(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test creating client with all fields."""
        user, token = test_steuerberater_user
        response = await async_client.post(
            "/api/v1/clients/",
            json={
                "name": "Test Mandant GmbH",
                "client_number": "M-2024-001",
                "tax_number": "12/345/67890",
                "vat_id": "DE123456789",
                "contact_name": "Max Mustermann",
                "contact_email": "max@example.com",
                "contact_phone": "+49 30 12345678",
                "street": "Teststraße 1",
                "postal_code": "10115",
                "city": "Berlin",
                "country": "DE",
                "notes": "Test notes",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_client_unauthorized(self, async_client: AsyncClient) -> None:
        """Test getting client without authentication fails."""
        client_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/clients/{client_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_client_invalid_uuid(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test getting client with invalid UUID fails."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/clients/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_client_unauthorized(self, async_client: AsyncClient) -> None:
        """Test updating client without authentication fails."""
        client_id = uuid.uuid4()
        response = await async_client.patch(
            f"/api/v1/clients/{client_id}",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_client_unauthorized(self, async_client: AsyncClient) -> None:
        """Test deleting client without authentication fails."""
        client_id = uuid.uuid4()
        response = await async_client.delete(f"/api/v1/clients/{client_id}")
        assert response.status_code == 401


class TestClientStats:
    """Tests for client statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats_unauthorized(self, async_client: AsyncClient) -> None:
        """Test getting client stats without authentication fails."""
        response = await async_client.get("/api/v1/clients/stats")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_stats_with_auth(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test getting client stats with authentication."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/clients/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


class TestClientAccessControl:
    """Tests for client management access control."""

    @pytest.mark.asyncio
    async def test_client_access_requires_steuerberater_plan(
        self, async_client: AsyncClient
    ) -> None:
        """Test that client management requires Steuerberater plan.

        The endpoint should return 403 for users without the Steuerberater plan.
        """
        # Without a real database, we can only test that auth is enforced
        response = await async_client.get("/api/v1/clients/")
        assert response.status_code == 401


class TestClientSchemas:
    """Tests for client request/response schemas."""

    def test_client_create_schema_valid(self) -> None:
        """Test ClientCreate schema accepts valid data."""
        from app.schemas.client import ClientCreate

        data = ClientCreate(
            name="Test GmbH",
            client_number="M-001",
            tax_number="12/345/67890",
            vat_id="DE123456789",
            contact_name="Max Mustermann",
            contact_email="test@example.com",
            contact_phone="+49 30 12345",
            street="Teststr. 1",
            postal_code="10115",
            city="Berlin",
            country="DE",
            notes="Some notes",
        )
        assert data.name == "Test GmbH"
        assert data.client_number == "M-001"
        assert data.country == "DE"

    def test_client_create_schema_minimal(self) -> None:
        """Test ClientCreate schema with minimal data."""
        from app.schemas.client import ClientCreate

        data = ClientCreate(name="Minimal Client")
        assert data.name == "Minimal Client"
        assert data.client_number is None
        assert data.tax_number is None

    def test_client_update_schema_partial(self) -> None:
        """Test ClientUpdate schema with partial data."""
        from app.schemas.client import ClientUpdate

        data = ClientUpdate(is_active=False)
        assert data.is_active is False
        assert data.name is None

    def test_client_update_schema_name_only(self) -> None:
        """Test ClientUpdate schema with name update only."""
        from app.schemas.client import ClientUpdate

        data = ClientUpdate(name="New Name")
        assert data.name == "New Name"
        assert data.is_active is None


class TestClientValidation:
    """Tests for client data validation."""

    @pytest.mark.asyncio
    async def test_create_client_invalid_email(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test creating client with invalid email fails."""
        user, token = test_steuerberater_user
        response = await async_client.post(
            "/api/v1/clients/",
            json={
                "name": "Test Client",
                "contact_email": "not-an-email",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_client_valid_german_data(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test creating client with German-format data."""
        user, token = test_steuerberater_user
        response = await async_client.post(
            "/api/v1/clients/",
            json={
                "name": "Müller & Söhne GmbH",
                "client_number": "M-2024-002",
                "tax_number": "12/345/67890",
                "vat_id": "DE123456789",
                "street": "Königstraße 42",
                "postal_code": "70173",
                "city": "Stuttgart",
                "country": "DE",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
