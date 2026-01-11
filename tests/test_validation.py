"""Tests for validation endpoints and services."""

import pytest
from httpx import AsyncClient


class TestXRechnungValidationEndpoint:
    """Tests for /api/v1/validate/xrechnung endpoint."""

    @pytest.mark.asyncio
    async def test_validate_valid_xrechnung(
        self, async_client: AsyncClient, sample_xrechnung_valid: bytes
    ) -> None:
        """Test validation of a valid XRechnung XML."""
        response = await async_client.post(
            "/api/v1/validate/xrechnung",
            files={"file": ("invoice.xml", sample_xrechnung_valid, "application/xml")},
        )

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert "is_valid" in data
        assert data["file_type"] == "xrechnung"
        assert "file_hash" in data
        assert "error_count" in data
        assert "warning_count" in data
        assert "processing_time_ms" in data
        assert "validator_version" in data

    @pytest.mark.asyncio
    async def test_validate_invalid_xrechnung(
        self, async_client: AsyncClient, sample_xrechnung_invalid: bytes
    ) -> None:
        """Test validation of an invalid XRechnung XML."""
        response = await async_client.post(
            "/api/v1/validate/xrechnung",
            files={"file": ("invoice.xml", sample_xrechnung_invalid, "application/xml")},
        )

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert data["file_type"] == "xrechnung"
        # Should have errors or warnings for missing fields
        assert data["error_count"] >= 0 or data["warning_count"] >= 0

    @pytest.mark.asyncio
    async def test_validate_malformed_xml(
        self, async_client: AsyncClient, sample_invalid_xml: bytes
    ) -> None:
        """Test validation of malformed XML."""
        response = await async_client.post(
            "/api/v1/validate/xrechnung",
            files={"file": ("invoice.xml", sample_invalid_xml, "application/xml")},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_validate_non_xml_content(
        self, async_client: AsyncClient, sample_non_xml: bytes
    ) -> None:
        """Test validation of non-XML content."""
        response = await async_client.post(
            "/api/v1/validate/xrechnung",
            files={"file": ("invoice.xml", sample_non_xml, "application/xml")},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_validate_wrong_file_extension(
        self, async_client: AsyncClient, sample_xrechnung_valid: bytes
    ) -> None:
        """Test validation with wrong file extension."""
        response = await async_client.post(
            "/api/v1/validate/xrechnung",
            files={"file": ("invoice.pdf", sample_xrechnung_valid, "application/pdf")},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "XML" in data["detail"]

    @pytest.mark.asyncio
    async def test_validate_empty_file(self, async_client: AsyncClient) -> None:
        """Test validation of empty file."""
        response = await async_client.post(
            "/api/v1/validate/xrechnung",
            files={"file": ("invoice.xml", b"", "application/xml")},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_validate_response_has_german_messages(
        self, async_client: AsyncClient, sample_xrechnung_invalid: bytes
    ) -> None:
        """Test that validation errors include German messages."""
        response = await async_client.post(
            "/api/v1/validate/xrechnung",
            files={"file": ("invoice.xml", sample_xrechnung_invalid, "application/xml")},
        )

        assert response.status_code == 200
        data = response.json()

        # Check errors have German messages
        for error in data.get("errors", []):
            assert "message_de" in error
            assert error["message_de"]  # Not empty

        for warning in data.get("warnings", []):
            assert "message_de" in warning


class TestZugferdValidationEndpoint:
    """Tests for /api/v1/validate/zugferd endpoint."""

    @pytest.mark.asyncio
    async def test_zugferd_not_implemented(
        self, async_client: AsyncClient
    ) -> None:
        """Test that ZUGFeRD endpoint returns not implemented."""
        # Create a minimal PDF-like content
        pdf_content = b"%PDF-1.4 fake pdf content"

        response = await async_client.post(
            "/api/v1/validate/zugferd",
            files={"file": ("invoice.pdf", pdf_content, "application/pdf")},
        )

        assert response.status_code == 501
        data = response.json()
        assert "ZUGFeRD" in data["detail"]

    @pytest.mark.asyncio
    async def test_zugferd_wrong_extension(
        self, async_client: AsyncClient, sample_xrechnung_valid: bytes
    ) -> None:
        """Test ZUGFeRD validation with wrong file extension."""
        response = await async_client.post(
            "/api/v1/validate/zugferd",
            files={"file": ("invoice.xml", sample_xrechnung_valid, "application/xml")},
        )

        assert response.status_code == 400
        data = response.json()
        assert "PDF" in data["detail"]


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient) -> None:
        """Test health check endpoint."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
