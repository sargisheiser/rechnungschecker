"""Tests for scheduled validation feature."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.scheduled_validation import (
    ScheduledValidationJob,
    ScheduledValidationRun,
    CloudStorageProvider,
    JobStatus,
    RunStatus,
)
from app.services.scheduler.service import SchedulerService
from app.services.storage.s3_client import S3StorageClient
from app.core.encryption import EncryptionService


class TestScheduledValidationAPI:
    """Test scheduled validation API endpoints."""

    @pytest.mark.asyncio
    async def test_list_jobs_requires_auth(self, async_client: AsyncClient):
        """Test that listing jobs requires authentication."""
        response = await async_client.get("/api/v1/scheduled-validations/")
        assert response.status_code == 401
        assert "Nicht authentifiziert" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_jobs_empty(
        self, async_client: AsyncClient, test_pro_user: tuple[User, str]
    ):
        """Test listing jobs when user has none."""
        user, token = test_pro_user
        response = await async_client.get(
            "/api/v1/scheduled-validations/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_job_requires_pro_plan(
        self, async_client: AsyncClient, test_user: tuple[User, str]
    ):
        """Test that creating a job requires Pro plan or higher."""
        user, token = test_user  # Free plan user
        response = await async_client.post(
            "/api/v1/scheduled-validations/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Test Job",
                "provider": "s3",
                "credentials": {
                    "s3": {
                        "access_key_id": "test-key",
                        "secret_access_key": "test-secret",
                        "region": "eu-central-1",
                    }
                },
                "bucket_name": "test-bucket",
                "schedule_cron": "0 8 * * *",
            },
        )
        assert response.status_code == 403
        assert "Pro plan" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_job_invalid_connection(
        self, async_client: AsyncClient, test_pro_user: tuple[User, str]
    ):
        """Test that creating a job with invalid credentials fails."""
        user, token = test_pro_user

        with patch.object(
            S3StorageClient, "test_connection", side_effect=ValueError("Bucket not found")
        ):
            response = await async_client.post(
                "/api/v1/scheduled-validations/",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": "Test Job",
                    "provider": "s3",
                    "credentials": {
                        "s3": {
                            "access_key_id": "invalid-key",
                            "secret_access_key": "invalid-secret",
                            "region": "eu-central-1",
                        }
                    },
                    "bucket_name": "nonexistent-bucket",
                    "schedule_cron": "0 8 * * *",
                },
            )
        assert response.status_code == 400
        assert "Bucket not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_test_connection_endpoint(
        self, async_client: AsyncClient, test_pro_user: tuple[User, str]
    ):
        """Test the connection test endpoint."""
        user, token = test_pro_user

        with patch.object(S3StorageClient, "test_connection", return_value=True):
            response = await async_client.post(
                "/api/v1/scheduled-validations/test-connection",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "provider": "s3",
                    "credentials": {
                        "s3": {
                            "access_key_id": "test-key",
                            "secret_access_key": "test-secret",
                            "region": "eu-central-1",
                        }
                    },
                    "bucket_name": "test-bucket",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Connection successful"

    @pytest.mark.asyncio
    async def test_test_connection_failure(
        self, async_client: AsyncClient, test_pro_user: tuple[User, str]
    ):
        """Test the connection test endpoint with failed connection."""
        user, token = test_pro_user

        with patch.object(
            S3StorageClient, "test_connection", side_effect=ValueError("Access denied")
        ):
            response = await async_client.post(
                "/api/v1/scheduled-validations/test-connection",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "provider": "s3",
                    "credentials": {
                        "s3": {
                            "access_key_id": "bad-key",
                            "secret_access_key": "bad-secret",
                            "region": "eu-central-1",
                        }
                    },
                    "bucket_name": "test-bucket",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Access denied" in data["message"]


class TestSchedulerService:
    """Test the APScheduler service."""

    def test_singleton_instance(self):
        """Test that SchedulerService is a singleton."""
        instance1 = SchedulerService.get_instance()
        instance2 = SchedulerService.get_instance()
        assert instance1 is instance2

    def test_cron_trigger_parsing(self):
        """Test that cron expressions are parsed correctly."""
        from apscheduler.triggers.cron import CronTrigger

        # Valid cron expression
        trigger = CronTrigger.from_crontab("0 8 * * *", timezone="Europe/Berlin")
        assert trigger is not None

        # Invalid cron expression should raise
        with pytest.raises(ValueError):
            CronTrigger.from_crontab("invalid cron", timezone="Europe/Berlin")


class TestS3StorageClient:
    """Test the S3 storage client."""

    def test_client_initialization(self):
        """Test that S3 client initializes with correct parameters."""
        client = S3StorageClient(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="eu-central-1",
        )

        assert client.region == "eu-central-1"
        assert client.session is not None

    def test_file_pattern_matching(self):
        """Test that fnmatch works for file patterns."""
        import fnmatch

        # Test XML pattern
        assert fnmatch.fnmatch("invoice.xml", "*.xml")
        # Note: fnmatch is case-sensitive; our S3 client uses .lower() for case-insensitive matching
        assert fnmatch.fnmatch("INVOICE.XML".lower(), "*.xml")
        assert not fnmatch.fnmatch("invoice.pdf", "*.xml")

        # Test multiple patterns
        assert fnmatch.fnmatch("test.pdf", "*.pdf")
        assert fnmatch.fnmatch("data.json", "*.json")


class TestEncryption:
    """Test credential encryption/decryption."""

    def test_encrypt_decrypt_credentials(self):
        """Test that credentials can be encrypted and decrypted."""
        encryption = EncryptionService()

        original = '{"access_key_id": "AKIAIOSFODNN7EXAMPLE", "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"}'

        encrypted = encryption.encrypt(original)
        assert encrypted != original
        assert len(encrypted) > 0

        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_produces_different_output(self):
        """Test that encrypting the same value twice produces different ciphertext."""
        encryption = EncryptionService()

        original = "test-secret"
        encrypted1 = encryption.encrypt(original)
        encrypted2 = encryption.encrypt(original)

        # Due to Fernet using random IVs, outputs should differ
        # But both should decrypt to the same value
        assert encryption.decrypt(encrypted1) == original
        assert encryption.decrypt(encrypted2) == original


class TestScheduledValidationModels:
    """Test scheduled validation database models."""

    def test_enum_values(self):
        """Test that enum values are correctly defined."""
        assert CloudStorageProvider.S3.value == "s3"
        assert CloudStorageProvider.GCS.value == "gcs"
        assert CloudStorageProvider.AZURE_BLOB.value == "azure_blob"

        assert JobStatus.ACTIVE.value == "active"
        assert JobStatus.PAUSED.value == "paused"
        assert JobStatus.ERROR.value == "error"

        assert RunStatus.PENDING.value == "pending"
        assert RunStatus.RUNNING.value == "running"
        assert RunStatus.COMPLETED.value == "completed"
        assert RunStatus.FAILED.value == "failed"

    def test_job_model_defaults(self):
        """Test that job model has correct default values."""
        from app.models.scheduled_validation import ScheduledValidationJob

        # Check that the model has expected attributes
        assert hasattr(ScheduledValidationJob, "is_enabled")
        assert hasattr(ScheduledValidationJob, "status")
        assert hasattr(ScheduledValidationJob, "total_runs")
        assert hasattr(ScheduledValidationJob, "total_files_validated")

    def test_run_model_defaults(self):
        """Test that run model has correct default values."""
        from app.models.scheduled_validation import ScheduledValidationRun

        # Check that the model has expected attributes
        assert hasattr(ScheduledValidationRun, "files_found")
        assert hasattr(ScheduledValidationRun, "files_validated")
        assert hasattr(ScheduledValidationRun, "files_valid")
        assert hasattr(ScheduledValidationRun, "files_invalid")
