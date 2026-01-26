"""Schemas for scheduled validation from cloud storage."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.scheduled_validation import CloudStorageProvider, JobStatus, RunStatus


class S3Credentials(BaseModel):
    """AWS S3 credentials."""

    access_key_id: str = Field(..., min_length=1)
    secret_access_key: str = Field(..., min_length=1)
    region: str = Field(default="eu-central-1")


class CloudCredentials(BaseModel):
    """Union of different provider credentials."""

    s3: S3Credentials | None = None
    # gcs: GCSCredentials | None = None  # Future
    # azure: AzureCredentials | None = None  # Future


class ScheduledValidationJobCreate(BaseModel):
    """Request to create a scheduled validation job."""

    name: str = Field(..., min_length=1, max_length=255)
    provider: CloudStorageProvider
    credentials: CloudCredentials
    bucket_name: str = Field(..., min_length=1, max_length=255)
    prefix: str | None = Field(default=None, max_length=500)
    file_pattern: str = Field(default="*.xml", max_length=100)
    schedule_cron: str = Field(..., min_length=5, max_length=100)
    timezone: str = Field(default="Europe/Berlin", max_length=50)
    delete_after_validation: bool = Field(default=False)
    move_to_folder: str | None = Field(default=None, max_length=500)
    webhook_url: str | None = Field(default=None, max_length=500)


class ScheduledValidationJobUpdate(BaseModel):
    """Request to update a scheduled validation job."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    prefix: str | None = Field(default=None, max_length=500)
    file_pattern: str | None = Field(default=None, max_length=100)
    schedule_cron: str | None = Field(default=None, min_length=5, max_length=100)
    timezone: str | None = Field(default=None, max_length=50)
    is_enabled: bool | None = None
    delete_after_validation: bool | None = None
    move_to_folder: str | None = Field(default=None, max_length=500)
    webhook_url: str | None = Field(default=None, max_length=500)


class ScheduledValidationJobResponse(BaseModel):
    """Response for a scheduled validation job."""

    id: UUID
    name: str
    provider: CloudStorageProvider
    bucket_name: str
    prefix: str | None
    file_pattern: str
    schedule_cron: str
    timezone: str
    is_enabled: bool
    status: JobStatus
    delete_after_validation: bool
    move_to_folder: str | None
    webhook_url: str | None
    last_run_at: datetime | None
    last_run_status: str | None
    total_runs: int
    total_files_validated: int
    total_files_valid: int
    total_files_invalid: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduledValidationRunResponse(BaseModel):
    """Response for a scheduled validation run."""

    id: UUID
    job_id: UUID
    status: RunStatus
    started_at: datetime
    completed_at: datetime | None
    files_found: int
    files_validated: int
    files_valid: int
    files_invalid: int
    files_failed: int
    error_message: str | None

    class Config:
        from_attributes = True


class ScheduledValidationFileResponse(BaseModel):
    """Response for a file in a scheduled validation run."""

    id: UUID
    file_key: str
    file_name: str
    file_size_bytes: int
    is_valid: bool | None
    error_count: int
    warning_count: int
    validation_log_id: UUID | None
    error_message: str | None

    class Config:
        from_attributes = True


class TestConnectionRequest(BaseModel):
    """Request to test cloud storage connection."""

    provider: CloudStorageProvider
    credentials: CloudCredentials
    bucket_name: str = Field(..., min_length=1, max_length=255)


class TestConnectionResponse(BaseModel):
    """Response for cloud storage connection test."""

    success: bool
    message: str
