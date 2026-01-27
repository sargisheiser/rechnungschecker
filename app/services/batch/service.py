"""Batch validation service for processing multiple files."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.batch import BatchFile, BatchFileStatus, BatchJob, BatchJobStatus
from app.schemas.batch import (
    BatchFileResult,
    BatchJobList,
    BatchJobResponse,
    BatchJobWithFiles,
    BatchResultsSummary,
)

logger = logging.getLogger(__name__)


class BatchService:
    """Service for managing batch validation jobs."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def create_job(
        self,
        user_id: UUID,
        name: str,
        files: list[tuple[str, bytes, int]],  # (filename, content, size)
        client_id: UUID | None = None,
    ) -> BatchJob:
        """Create a new batch validation job.

        Args:
            user_id: User creating the job
            name: Job name
            files: List of (filename, content, size) tuples
            client_id: Optional client ID for filtering

        Returns:
            Created BatchJob
        """
        job = BatchJob(
            user_id=user_id,
            client_id=client_id,
            name=name,
            total_files=len(files),
        )
        self.db.add(job)
        await self.db.flush()

        # Add files to job
        for filename, content, size in files:
            batch_file = BatchFile(
                batch_job_id=job.id,
                filename=filename,
                file_content=content,
                file_size_bytes=size,
            )
            self.db.add(batch_file)

        await self.db.flush()
        logger.info(f"Created batch job: id={job.id}, user={user_id}, files={len(files)}")
        return job

    async def get_job(self, job_id: UUID, user_id: UUID) -> BatchJob | None:
        """Get a batch job by ID.

        Args:
            job_id: Job ID
            user_id: User ID for ownership check

        Returns:
            BatchJob if found and owned by user
        """
        result = await self.db.execute(
            select(BatchJob)
            .options(
                selectinload(BatchJob.files).selectinload(BatchFile.validation)
            )
            .where(BatchJob.id == job_id, BatchJob.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_jobs(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> BatchJobList:
        """Get paginated list of user's batch jobs.

        Args:
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Paginated job list
        """
        offset = (page - 1) * page_size

        # Get total count
        count_query = select(func.count(BatchJob.id)).where(
            BatchJob.user_id == user_id
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get jobs
        query = (
            select(BatchJob)
            .where(BatchJob.user_id == user_id)
            .order_by(BatchJob.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        jobs = result.scalars().all()

        return BatchJobList(
            items=[
                BatchJobResponse(
                    id=job.id,
                    name=job.name,
                    status=job.status,
                    total_files=job.total_files,
                    processed_files=job.processed_files,
                    successful_count=job.successful_count,
                    failed_count=job.failed_count,
                    progress_percent=job.progress_percent,
                    error_message=job.error_message,
                    created_at=job.created_at,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                    client_id=job.client_id,
                )
                for job in jobs
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_job_with_files(
        self,
        job_id: UUID,
        user_id: UUID,
    ) -> BatchJobWithFiles | None:
        """Get batch job with file details.

        Args:
            job_id: Job ID
            user_id: User ID for ownership check

        Returns:
            BatchJobWithFiles if found
        """
        job = await self.get_job(job_id, user_id)
        if not job:
            return None

        from app.schemas.batch import BatchFileResponse

        return BatchJobWithFiles(
            id=job.id,
            name=job.name,
            status=job.status,
            total_files=job.total_files,
            processed_files=job.processed_files,
            successful_count=job.successful_count,
            failed_count=job.failed_count,
            progress_percent=job.progress_percent,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            client_id=job.client_id,
            files=[
                BatchFileResponse(
                    id=f.id,
                    filename=f.filename,
                    file_size_bytes=f.file_size_bytes,
                    status=f.status,
                    validation_id=f.validation_id,
                    error_message=f.error_message,
                    processed_at=f.processed_at,
                )
                for f in job.files
            ],
        )

    async def get_pending_files(self, job_id: UUID) -> list[BatchFile]:
        """Get pending files for a job.

        Args:
            job_id: Job ID

        Returns:
            List of pending BatchFile objects
        """
        result = await self.db.execute(
            select(BatchFile)
            .where(
                BatchFile.batch_job_id == job_id,
                BatchFile.status == BatchFileStatus.PENDING,
            )
            .order_by(BatchFile.created_at)
        )
        return list(result.scalars().all())

    async def update_file_status(
        self,
        file_id: UUID,
        status: BatchFileStatus,
        validation_id: UUID | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update a file's status.

        Args:
            file_id: File ID
            status: New status
            validation_id: Validation log ID if completed
            error_message: Error message if failed
        """
        result = await self.db.execute(
            select(BatchFile).where(BatchFile.id == file_id)
        )
        file = result.scalar_one_or_none()
        if not file:
            return

        file.status = status
        file.processed_at = datetime.now(UTC).replace(tzinfo=None)

        if validation_id:
            file.validation_id = validation_id
        if error_message:
            file.error_message = error_message

        # Clear file content after processing
        file.file_content = None

        await self.db.flush()

    async def update_job_progress(
        self,
        job_id: UUID,
        successful: bool,
    ) -> None:
        """Update job progress after processing a file.

        Args:
            job_id: Job ID
            successful: Whether the file was processed successfully
        """
        result = await self.db.execute(
            select(BatchJob).where(BatchJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return

        job.increment_progress(successful)

        # Check if job is complete
        if job.processed_files >= job.total_files:
            job.mark_completed()

        await self.db.flush()

    async def cancel_job(self, job_id: UUID, user_id: UUID) -> bool:
        """Cancel a batch job.

        Args:
            job_id: Job ID
            user_id: User ID for ownership check

        Returns:
            True if cancelled successfully
        """
        job = await self.get_job(job_id, user_id)
        if not job:
            return False

        if job.is_complete:
            return False

        job.status = BatchJobStatus.CANCELLED
        job.completed_at = datetime.now(UTC).replace(tzinfo=None)

        # Mark pending files as skipped
        pending_files = await self.get_pending_files(job_id)
        for file in pending_files:
            file.mark_skipped("Job cancelled")

        await self.db.flush()
        logger.info(f"Cancelled batch job: id={job_id}")
        return True

    async def delete_job(self, job_id: UUID, user_id: UUID) -> bool:
        """Delete a batch job and its files.

        Args:
            job_id: Job ID
            user_id: User ID for ownership check

        Returns:
            True if deleted successfully
        """
        job = await self.get_job(job_id, user_id)
        if not job:
            return False

        await self.db.delete(job)
        await self.db.flush()
        logger.info(f"Deleted batch job: id={job_id}")
        return True

    async def get_results_summary(
        self,
        job_id: UUID,
        user_id: UUID,
    ) -> BatchResultsSummary | None:
        """Get summary of batch validation results.

        Args:
            job_id: Job ID
            user_id: User ID for ownership check

        Returns:
            BatchResultsSummary if found
        """
        job = await self.get_job(job_id, user_id)
        if not job:
            return None

        # Get validation results for completed files
        valid_count = 0
        invalid_count = 0
        results = []

        for file in job.files:
            result = BatchFileResult(
                filename=file.filename,
                is_valid=None,
                error_count=0,
                warning_count=0,
                validation_id=file.validation_id,
                error_message=file.error_message,
            )

            # Use eager-loaded validation (no extra query needed)
            if file.validation:
                result.is_valid = file.validation.is_valid
                result.error_count = file.validation.error_count
                result.warning_count = file.validation.warning_count
                if file.validation.is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1

            results.append(result)

        return BatchResultsSummary(
            job_id=job.id,
            job_name=job.name,
            status=job.status,
            total_files=job.total_files,
            successful_count=job.successful_count,
            failed_count=job.failed_count,
            valid_count=valid_count,
            invalid_count=invalid_count,
            results=results,
        )
