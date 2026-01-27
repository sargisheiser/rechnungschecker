"""Batch validation models for processing multiple files."""

import enum
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, LargeBinary, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BatchJobStatus(str, enum.Enum):
    """Status of a batch validation job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchFileStatus(str, enum.Enum):
    """Status of a file within a batch job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class BatchJob(Base):
    """Batch validation job for processing multiple files."""

    __tablename__ = "batch_jobs"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Job metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[BatchJobStatus] = mapped_column(
        Enum(BatchJobStatus, name="batchjobstatus", values_callable=lambda x: [e.value for e in x], create_type=False),
        default=BatchJobStatus.PENDING,
    )

    # Progress tracking
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    processed_files: Mapped[int] = mapped_column(Integer, default=0)
    successful_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    files: Mapped[list["BatchFile"]] = relationship(
        "BatchFile", back_populates="batch_job", cascade="all, delete-orphan"
    )
    user = relationship("User", back_populates="batch_jobs")
    client = relationship("Client", back_populates="batch_jobs")

    def start_processing(self) -> None:
        """Mark job as processing."""
        self.status = BatchJobStatus.PROCESSING
        self.started_at = datetime.now(UTC).replace(tzinfo=None)

    def mark_completed(self) -> None:
        """Mark job as completed."""
        self.status = BatchJobStatus.COMPLETED
        self.completed_at = datetime.now(UTC).replace(tzinfo=None)

    def mark_failed(self, error_message: str) -> None:
        """Mark job as failed."""
        self.status = BatchJobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(UTC).replace(tzinfo=None)

    def increment_progress(self, successful: bool) -> None:
        """Update progress counters."""
        self.processed_files += 1
        if successful:
            self.successful_count += 1
        else:
            self.failed_count += 1

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.total_files == 0:
            return 0
        return round(self.processed_files / self.total_files * 100, 1)

    @property
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.status in (
            BatchJobStatus.COMPLETED,
            BatchJobStatus.FAILED,
            BatchJobStatus.CANCELLED,
        )


class BatchFile(Base):
    """Individual file within a batch job."""

    __tablename__ = "batch_files"
    __table_args__ = (
        Index("ix_batch_file_job_status", "batch_job_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    batch_job_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batch_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File info
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    file_content: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    # Status
    status: Mapped[BatchFileStatus] = mapped_column(
        Enum(
            BatchFileStatus, name="batchfilestatus",
            values_callable=lambda x: [e.value for e in x], create_type=False
        ),
        default=BatchFileStatus.PENDING,
    )

    # Result reference
    validation_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("validation_logs.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Error info
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    batch_job: Mapped["BatchJob"] = relationship("BatchJob", back_populates="files")
    validation = relationship("ValidationLog")

    def mark_processing(self) -> None:
        """Mark file as processing."""
        self.status = BatchFileStatus.PROCESSING

    def mark_completed(self, validation_id: UUID) -> None:
        """Mark file as completed with validation result."""
        self.status = BatchFileStatus.COMPLETED
        self.validation_id = validation_id
        self.processed_at = datetime.now(UTC).replace(tzinfo=None)
        # Clear file content to save space
        self.file_content = None

    def mark_failed(self, error_message: str) -> None:
        """Mark file as failed."""
        self.status = BatchFileStatus.FAILED
        self.error_message = error_message
        self.processed_at = datetime.now(UTC).replace(tzinfo=None)
        # Clear file content to save space
        self.file_content = None

    def mark_skipped(self, reason: str) -> None:
        """Mark file as skipped."""
        self.status = BatchFileStatus.SKIPPED
        self.error_message = reason
        self.processed_at = datetime.now(UTC).replace(tzinfo=None)
        self.file_content = None
