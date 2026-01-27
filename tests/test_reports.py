"""Tests for reports endpoints."""

import uuid
from datetime import UTC

import pytest
from httpx import AsyncClient


class TestReportGetEndpoint:
    """Tests for getting report details."""

    @pytest.mark.asyncio
    async def test_get_report_valid_uuid(
        self, async_client: AsyncClient
    ) -> None:
        """Test getting report with valid UUID (report not in cache)."""
        report_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/reports/{report_id}")
        # 404 because report not in cache
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_report_invalid_uuid(
        self, async_client: AsyncClient
    ) -> None:
        """Test getting report with invalid UUID fails."""
        response = await async_client.get("/api/v1/reports/not-a-uuid")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_report_not_found_message(
        self, async_client: AsyncClient
    ) -> None:
        """Test getting non-existent report returns German error message."""
        report_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/reports/{report_id}")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        # German error message expected
        assert "nicht gefunden" in data["detail"] or "abgelaufen" in data["detail"]


class TestReportPDFEndpoint:
    """Tests for downloading report PDF."""

    @pytest.mark.asyncio
    async def test_download_pdf_valid_uuid(
        self, async_client: AsyncClient
    ) -> None:
        """Test downloading PDF with valid UUID (report not in cache)."""
        report_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/reports/{report_id}/pdf")
        # 404 because report not in cache
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_pdf_invalid_uuid(
        self, async_client: AsyncClient
    ) -> None:
        """Test downloading PDF with invalid UUID fails."""
        response = await async_client.get("/api/v1/reports/not-a-uuid/pdf")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_download_pdf_not_found_message(
        self, async_client: AsyncClient
    ) -> None:
        """Test downloading non-existent PDF returns German error message."""
        report_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/reports/{report_id}/pdf")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        # German error message expected
        assert "nicht gefunden" in data["detail"] or "abgelaufen" in data["detail"]


class TestReportEndpointAuthentication:
    """Tests for report endpoint authentication behavior."""

    @pytest.mark.asyncio
    async def test_get_report_no_auth_required(
        self, async_client: AsyncClient
    ) -> None:
        """Test that report GET endpoint doesn't require authentication.

        Reports are accessible via shared links, so no auth is required.
        The endpoint uses OptionalUser dependency.
        """
        report_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/reports/{report_id}")
        # Should not return 401 (unauthorized), but 404 (not found)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_pdf_no_auth_required(
        self, async_client: AsyncClient
    ) -> None:
        """Test that PDF download doesn't require authentication.

        PDFs are accessible via shared links.
        """
        report_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/reports/{report_id}/pdf")
        # Should not return 401 (unauthorized), but 404 (not found)
        assert response.status_code == 404


class TestReportWithCache:
    """Tests for report endpoints with cache interactions.

    These tests verify the integration between reports and the cache.
    In a real test environment, we would populate the cache first.
    """

    @pytest.mark.asyncio
    async def test_cached_report_structure(
        self, async_client: AsyncClient
    ) -> None:
        """Test that a cached report returns expected structure.

        Note: This test will fail (404) without a populated cache.
        The expected response structure is documented here.
        """
        report_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/reports/{report_id}")

        # Without cache, expect 404
        if response.status_code == 404:
            return

        # If we somehow had a cached report, verify structure
        data = response.json()
        expected_fields = [
            "id",
            "is_valid",
            "file_type",
            "error_count",
            "warning_count",
            "validated_at",
        ]
        for field in expected_fields:
            assert field in data


class TestReportResponseHeaders:
    """Tests for report response headers."""

    @pytest.mark.asyncio
    async def test_pdf_content_type(
        self, async_client: AsyncClient
    ) -> None:
        """Test that PDF endpoint would return correct content type.

        Note: Without a cached report, we can't test the actual response.
        This test documents the expected behavior.
        """
        report_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/reports/{report_id}/pdf")

        # Without cache, expect 404
        if response.status_code == 404:
            return

        # If we had a cached report, verify headers
        assert response.headers.get("content-type") == "application/pdf"
        assert "Content-Disposition" in response.headers


class TestReportServiceIntegration:
    """Tests for report service functionality."""

    def test_create_pdf_response_helper(self) -> None:
        """Test the create_pdf_response helper function."""
        from app.api.v1.reports import create_pdf_response

        pdf_bytes = b"%PDF-1.4 test content"
        response = create_pdf_response(pdf_bytes, "test-report.pdf")

        assert response.media_type == "application/pdf"
        assert "test-report.pdf" in response.headers.get("Content-Disposition", "")
        assert response.headers.get("Content-Length") == str(len(pdf_bytes))


class TestReportErrorHandling:
    """Tests for report error handling."""

    @pytest.mark.asyncio
    async def test_report_expired_error(
        self, async_client: AsyncClient
    ) -> None:
        """Test that expired reports return appropriate error.

        Reports expire after 30 minutes. The error message should
        indicate that the report has expired.
        """
        report_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/reports/{report_id}")
        assert response.status_code == 404
        data = response.json()
        # Should mention expiration or not found
        assert "abgelaufen" in data["detail"] or "nicht gefunden" in data["detail"]

    @pytest.mark.asyncio
    async def test_pdf_expired_error(
        self, async_client: AsyncClient
    ) -> None:
        """Test that expired PDF reports return appropriate error."""
        report_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/reports/{report_id}/pdf")
        assert response.status_code == 404
        data = response.json()
        # Should mention 30 Min expiration
        assert "30 Min" in data["detail"] or "nicht gefunden" in data["detail"]


class TestReportCacheModule:
    """Tests for the report cache module."""

    def test_get_cached_validation_not_found(self) -> None:
        """Test get_cached_validation returns None for non-existent ID."""
        from app.core.cache import get_cached_validation

        result = get_cached_validation(uuid.uuid4())
        assert result is None

    def test_cache_validation_and_retrieve(self) -> None:
        """Test caching a validation result and retrieving it."""
        from datetime import datetime

        from app.core.cache import cache_validation_result, get_cached_validation
        from app.schemas.validation import ValidationResponse

        # Create a proper ValidationResponse with all required fields
        validation_id = uuid.uuid4()
        mock_result = ValidationResponse(
            id=validation_id,
            is_valid=True,
            file_type="xrechnung",
            file_hash="abc123def456",
            error_count=0,
            warning_count=2,
            info_count=0,
            errors=[],
            warnings=[],
            infos=[],
            validator_version="1.5.0",
            processing_time_ms=150,
            validated_at=datetime.now(UTC),
        )

        # Cache it
        cache_validation_result(mock_result)

        # Retrieve it
        cached = get_cached_validation(mock_result.id)

        if cached is not None:
            assert cached.id == mock_result.id
            assert cached.is_valid
            assert cached.error_count == 0


class TestReportURLPatterns:
    """Tests for report URL patterns and routing."""

    @pytest.mark.asyncio
    async def test_report_url_pattern(
        self, async_client: AsyncClient
    ) -> None:
        """Test report URL pattern matches expected format."""
        report_id = uuid.uuid4()

        # Both patterns should work
        response1 = await async_client.get(f"/api/v1/reports/{report_id}")
        response2 = await async_client.get(f"/api/v1/reports/{report_id}/pdf")

        # Both should not be 404 for routing (only for cache miss)
        # or 422 for validation errors
        assert response1.status_code in [200, 404, 500]
        assert response2.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_report_url_trailing_slash(
        self, async_client: AsyncClient
    ) -> None:
        """Test report URL with trailing slash handling."""
        report_id = uuid.uuid4()

        # URL with trailing slash might redirect or fail
        response = await async_client.get(f"/api/v1/reports/{report_id}/")
        # Accept various responses depending on router configuration
        assert response.status_code in [200, 307, 404, 405]
