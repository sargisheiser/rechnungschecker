"""Scheduled validation models for cloud storage integration."""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CloudStorageProvider(str, enum.Enum):
    """Supported cloud storage providers."""

    S3 = "s3"
    GCS = "gcs"
    AZURE_BLOB = "azure_blob"


class JobStatus(str, enum.Enum):
    """Scheduled job status."""

    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class RunStatus(str, enum.Enum):
    """Scheduled run status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScheduledValidationJob(Base):
    """Scheduled validation job configuration."""

    __tablename__ = "scheduled_validation_jobs"
    __table_args__ = (Index("ix_scheduled_validation_jobs_user_id", "user_id"),)

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Cloud storage configuration
    provider: Mapped[CloudStorageProvider] = mapped_column(
        Enum(CloudStorageProvider), nullable=False
    )
    encrypted_credentials: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Fernet encrypted JSON
    bucket_name: Mapped[str] = mapped_column(String(255), nullable=False)
    prefix: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # e.g., "invoices/pending/"
    file_pattern: Mapped[str] = mapped_column(
        String(100), default="*.xml"
    )  # glob pattern

    # Schedule configuration
    schedule_cron: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "0 8 * * *"
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Berlin")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.ACTIVE)

    # Post-validation options
    delete_after_validation: Mapped[bool] = mapped_column(Boolean, default=False)
    move_to_folder: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # e.g., "invoices/validated/"
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Statistics
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_run_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_runs: Mapped[int] = mapped_column(Integer, default=0)
    total_files_validated: Mapped[int] = mapped_column(Integer, default=0)
    total_files_valid: Mapped[int] = mapped_column(Integer, default=0)
    total_files_invalid: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="scheduled_validation_jobs")
    runs = relationship(
        "ScheduledValidationRun",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="desc(ScheduledValidationRun.started_at)",
    )


class ScheduledValidationRun(Base):
    """A single execution run of a scheduled validation job."""

    __tablename__ = "scheduled_validation_runs"
    __table_args__ = (Index("ix_scheduled_validation_runs_job_id", "job_id"),)

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    job_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scheduled_validation_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.PENDING)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # File statistics
    files_found: Mapped[int] = mapped_column(Integer, default=0)
    files_validated: Mapped[int] = mapped_column(Integer, default=0)
    files_valid: Mapped[int] = mapped_column(Integer, default=0)
    files_invalid: Mapped[int] = mapped_column(Integer, default=0)
    files_failed: Mapped[int] = mapped_column(Integer, default=0)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    job = relationship("ScheduledValidationJob", back_populates="runs")
    files = relationship(
        "ScheduledValidationFile",
        back_populates="run",
        cascade="all, delete-orphan",
    )


class ScheduledValidationFile(Base):
    """Individual file processed in a scheduled validation run."""

    __tablename__ = "scheduled_validation_files"
    __table_args__ = (Index("ix_scheduled_validation_files_run_id", "run_id"),)

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    run_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scheduled_validation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )

    file_key: Mapped[str] = mapped_column(
        String(1000), nullable=False
    )  # S3 key / full path
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    # Validation results
    is_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    validation_log_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("validation_logs.id", ondelete="SET NULL"),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # If processing failed

    # Relationships
    run = relationship("ScheduledValidationRun", back_populates="files")
