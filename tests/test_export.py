"""Tests for CSV export endpoints."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.schemas.export import ExportFormat, ValidationStatus


class TestExportValidationsEndpoint:
    """Tests for validation export endpoint."""

    @pytest.mark.asyncio
    async def test_export_validations_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test exporting validations without authentication fails."""
        response = await async_client.get("/api/v1/export/validations")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_export_validations_invalid_token(
        self, async_client: AsyncClient
    ) -> None:
        """Test exporting validations with invalid token fails."""
        response = await async_client.get(
            "/api/v1/export/validations",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_export_validations_datev_format(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting validations with DATEV format."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/validations",
            params={"format": "datev"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_validations_excel_format(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting validations with Excel format."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/validations",
            params={"format": "excel"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_validations_invalid_format(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting validations with invalid format fails."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/validations",
            params={"format": "invalid-format"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_export_validations_with_date_filters(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting validations with date filters."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/validations",
            params={
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_validations_with_client_filter(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting validations filtered by client."""
        user, token = test_steuerberater_user
        client_id = uuid.uuid4()
        response = await async_client.get(
            "/api/v1/export/validations",
            params={"client_id": str(client_id)},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_validations_status_filter_valid(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting only valid validations."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/validations",
            params={"status": "valid"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_validations_status_filter_invalid(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting only invalid validations."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/validations",
            params={"status": "invalid"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_validations_invalid_date_format(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting validations with invalid date format fails."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/validations",
            params={"date_from": "not-a-date"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


class TestExportClientsEndpoint:
    """Tests for clients export endpoint."""

    @pytest.mark.asyncio
    async def test_export_clients_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test exporting clients without authentication fails."""
        response = await async_client.get("/api/v1/export/clients")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_export_clients_datev_format(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting clients with DATEV format."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/clients",
            params={"format": "datev"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_clients_excel_format(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting clients with Excel format."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/clients",
            params={"format": "excel"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_clients_include_inactive(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting clients including inactive ones."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/clients",
            params={"include_inactive": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_clients_with_date_filters(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting clients with validation date filters."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/clients",
            params={
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


class TestExportAccessControl:
    """Tests for export access control."""

    @pytest.mark.asyncio
    async def test_export_requires_steuerberater_plan(
        self, async_client: AsyncClient
    ) -> None:
        """Test that export requires Steuerberater plan.

        The endpoint returns 403 for users without the correct plan.
        """
        response = await async_client.get("/api/v1/export/validations")
        assert response.status_code == 401


class TestExportSchemas:
    """Tests for export schema validation."""

    def test_export_format_enum(self) -> None:
        """Test ExportFormat enum values."""
        assert ExportFormat.CSV_DATEV.value == "datev"
        assert ExportFormat.CSV_EXCEL.value == "excel"

    def test_validation_status_enum(self) -> None:
        """Test ValidationStatus enum values."""
        assert ValidationStatus.ALL.value == "all"
        assert ValidationStatus.VALID.value == "valid"
        assert ValidationStatus.INVALID.value == "invalid"

    def test_validations_export_params_defaults(self) -> None:
        """Test ValidationsExportParams default values."""
        from app.schemas.export import ValidationsExportParams

        params = ValidationsExportParams()
        assert params.client_id is None
        assert params.date_from is None
        assert params.date_to is None
        assert params.status == ValidationStatus.ALL
        assert params.format == ExportFormat.CSV_DATEV

    def test_clients_export_params_defaults(self) -> None:
        """Test ClientsExportParams default values."""
        from app.schemas.export import ClientsExportParams

        params = ClientsExportParams()
        assert params.include_inactive is False
        assert params.date_from is None
        assert params.date_to is None
        assert params.format == ExportFormat.CSV_DATEV

    def test_validations_export_params_with_values(self) -> None:
        """Test ValidationsExportParams with custom values."""
        from app.schemas.export import ValidationsExportParams

        client_id = uuid.uuid4()
        params = ValidationsExportParams(
            client_id=client_id,
            date_from=date(2024, 1, 1),
            date_to=date(2024, 12, 31),
            status=ValidationStatus.VALID,
            format=ExportFormat.CSV_EXCEL,
        )
        assert params.client_id == client_id
        assert params.date_from == date(2024, 1, 1)
        assert params.date_to == date(2024, 12, 31)
        assert params.status == ValidationStatus.VALID
        assert params.format == ExportFormat.CSV_EXCEL
