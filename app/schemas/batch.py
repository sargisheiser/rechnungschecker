"""Pydantic schemas for batch validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.batch import BatchFileStatus, BatchJobStatus


class BatchJobCreate(BaseModel):
    """Request to create a batch validation job."""

    name: str = Field(default="Batch Validation", max_length=255)
    client_id: UUID | None = None


class BatchFileResponse(BaseModel):
    """Response for a single file in a batch."""

    id: UUID
    filename: str
    file_size_bytes: int
    status: BatchFileStatus
    validation_id: UUID | None
    error_message: str | None
    processed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class BatchJobResponse(BaseModel):
    """Response for a batch job."""

    id: UUID
    name: str
    status: BatchJobStatus
    total_files: int
    processed_files: int
    successful_count: int
    failed_count: int
    progress_percent: float
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    client_id: UUID | None

    model_config = ConfigDict(from_attributes=True)


class BatchJobCreated(BaseModel):
    """Response when batch job is created."""

    id: UUID
    name: str
    total_files: int
    status: BatchJobStatus
    message: str


class BatchJobWithFiles(BatchJobResponse):
    """Batch job response including file details."""

    files: list[BatchFileResponse]


class BatchJobList(BaseModel):
    """Paginated list of batch jobs."""

    items: list[BatchJobResponse]
    total: int
    page: int
    page_size: int


class BatchFileResult(BaseModel):
    """Result summary for a file in batch."""

    filename: str
    is_valid: bool | None
    error_count: int
    warning_count: int
    validation_id: UUID | None
    error_message: str | None


class BatchResultsSummary(BaseModel):
    """Summary of batch validation results."""

    job_id: UUID
    job_name: str
    status: BatchJobStatus
    total_files: int
    successful_count: int
    failed_count: int
    valid_count: int
    invalid_count: int
    results: list[BatchFileResult]
