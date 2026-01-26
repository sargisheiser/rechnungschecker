"""Service for managing scheduled validation jobs from cloud storage."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import async_session_maker
from app.core.encryption import EncryptionService
from app.models.scheduled_validation import (
    CloudStorageProvider,
    JobStatus,
    RunStatus,
    ScheduledValidationFile,
    ScheduledValidationJob,
    ScheduledValidationRun,
)
from app.schemas.scheduled_validation import (
    CloudCredentials,
    ScheduledValidationJobCreate,
)
from app.services.scheduler.service import SchedulerService
from app.services.storage.s3_client import S3StorageClient
from app.services.validation_history import ValidationHistoryService
from app.services.validator.xrechnung import XRechnungValidator
from app.services.validator.zugferd import ZUGFeRDValidator

logger = logging.getLogger(__name__)
encryption = EncryptionService()


class ScheduledValidationService:
    """Service for managing scheduled validation jobs."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def create_job(
        self,
        user_id: UUID,
        data: ScheduledValidationJobCreate,
    ) -> ScheduledValidationJob:
        """Create a new scheduled validation job.

        Args:
            user_id: The user creating the job
            data: Job configuration

        Returns:
            The created job
        """
        # Encrypt credentials
        credentials_json = data.credentials.model_dump_json()
        encrypted_creds = encryption.encrypt(credentials_json)

        job = ScheduledValidationJob(
            user_id=user_id,
            name=data.name,
            provider=data.provider,
            encrypted_credentials=encrypted_creds,
            bucket_name=data.bucket_name,
            prefix=data.prefix,
            file_pattern=data.file_pattern,
            schedule_cron=data.schedule_cron,
            timezone=data.timezone,
            delete_after_validation=data.delete_after_validation,
            move_to_folder=data.move_to_folder,
            webhook_url=data.webhook_url,
        )
        self.db.add(job)
        await self.db.flush()

        # Register with scheduler
        scheduler = SchedulerService.get_instance()
        scheduler.add_job(
            job_id=job.id,
            cron_expression=data.schedule_cron,
            timezone=data.timezone,
            func=run_scheduled_validation_job,
            args=(job.id,),
        )

        logger.info(f"Created scheduled validation job {job.id} for user {user_id}")
        return job

    async def get_job(
        self,
        job_id: UUID,
        user_id: UUID,
    ) -> ScheduledValidationJob | None:
        """Get a job by ID for a specific user.

        Args:
            job_id: The job ID
            user_id: The user ID (for authorization)

        Returns:
            The job or None if not found/not authorized
        """
        result = await self.db.execute(
            select(ScheduledValidationJob)
            .where(ScheduledValidationJob.id == job_id)
            .where(ScheduledValidationJob.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_jobs(self, user_id: UUID) -> list[ScheduledValidationJob]:
        """Get all jobs for a user.

        Args:
            user_id: The user ID

        Returns:
            List of jobs ordered by creation date (newest first)
        """
        result = await self.db.execute(
            select(ScheduledValidationJob)
            .where(ScheduledValidationJob.user_id == user_id)
            .order_by(ScheduledValidationJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_job(
        self,
        job: ScheduledValidationJob,
        **kwargs,
    ) -> ScheduledValidationJob:
        """Update a job's configuration.

        Args:
            job: The job to update
            **kwargs: Fields to update

        Returns:
            The updated job
        """
        for key, value in kwargs.items():
            if value is not None and hasattr(job, key):
                setattr(job, key, value)

        # Update scheduler if schedule changed
        schedule_changed = any(
            k in kwargs for k in ["schedule_cron", "timezone", "is_enabled"]
        )
        if schedule_changed:
            scheduler = SchedulerService.get_instance()
            if job.is_enabled:
                scheduler.add_job(
                    job_id=job.id,
                    cron_expression=job.schedule_cron,
                    timezone=job.timezone,
                    func=run_scheduled_validation_job,
                    args=(job.id,),
                )
                job.status = JobStatus.ACTIVE
            else:
                scheduler.remove_job(job.id)
                job.status = JobStatus.PAUSED

        logger.info(f"Updated scheduled validation job {job.id}")
        return job

    async def delete_job(self, job: ScheduledValidationJob) -> None:
        """Delete a job and remove from scheduler.

        Args:
            job: The job to delete
        """
        scheduler = SchedulerService.get_instance()
        scheduler.remove_job(job.id)
        await self.db.delete(job)
        logger.info(f"Deleted scheduled validation job {job.id}")

    async def get_job_runs(
        self,
        job_id: UUID,
        limit: int = 20,
    ) -> list[ScheduledValidationRun]:
        """Get run history for a job.

        Args:
            job_id: The job ID
            limit: Maximum number of runs to return

        Returns:
            List of runs ordered by start time (newest first)
        """
        result = await self.db.execute(
            select(ScheduledValidationRun)
            .where(ScheduledValidationRun.job_id == job_id)
            .order_by(ScheduledValidationRun.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_run_files(self, run_id: UUID) -> list[ScheduledValidationFile]:
        """Get files processed in a run.

        Args:
            run_id: The run ID

        Returns:
            List of files in the run
        """
        result = await self.db.execute(
            select(ScheduledValidationFile).where(
                ScheduledValidationFile.run_id == run_id
            )
        )
        return list(result.scalars().all())

    async def test_connection(
        self,
        provider: CloudStorageProvider,
        credentials: CloudCredentials,
        bucket_name: str,
    ) -> tuple[bool, str]:
        """Test cloud storage connection.

        Args:
            provider: The cloud storage provider
            credentials: The credentials to test
            bucket_name: The bucket to test access to

        Returns:
            Tuple of (success, message)
        """
        try:
            if provider == CloudStorageProvider.S3 and credentials.s3:
                client = S3StorageClient(
                    access_key_id=credentials.s3.access_key_id,
                    secret_access_key=credentials.s3.secret_access_key,
                    region=credentials.s3.region,
                )
                await client.test_connection(bucket_name)
                return True, "Connection successful"
            else:
                return False, f"Unsupported provider: {provider}"
        except ValueError as e:
            return False, str(e)
        except PermissionError as e:
            return False, str(e)
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, f"Connection failed: {str(e)}"


async def run_scheduled_validation_job(job_id: UUID) -> None:
    """Background task to run a scheduled validation job.

    This function is called by APScheduler when a job is triggered.

    Args:
        job_id: The ID of the job to run
    """
    logger.info(f"Starting scheduled validation job {job_id}")

    async with async_session_maker() as db:
        # Get job with user
        result = await db.execute(
            select(ScheduledValidationJob)
            .options(selectinload(ScheduledValidationJob.user))
            .where(ScheduledValidationJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            logger.error(f"Job {job_id} not found")
            return

        if not job.is_enabled:
            logger.info(f"Job {job_id} is disabled, skipping")
            return

        # Create run record
        run = ScheduledValidationRun(job_id=job.id, status=RunStatus.RUNNING)
        db.add(run)
        await db.flush()

        try:
            # Decrypt credentials
            creds_json = encryption.decrypt(job.encrypted_credentials)
            creds = CloudCredentials.model_validate_json(creds_json)

            # Get storage client
            if job.provider == CloudStorageProvider.S3 and creds.s3:
                client = S3StorageClient(
                    access_key_id=creds.s3.access_key_id,
                    secret_access_key=creds.s3.secret_access_key,
                    region=creds.s3.region,
                )
            else:
                raise ValueError(f"Unsupported provider: {job.provider}")

            # List files
            files = await client.list_files(
                bucket=job.bucket_name,
                prefix=job.prefix or "",
                pattern=job.file_pattern,
            )
            run.files_found = len(files)
            logger.info(f"Job {job_id}: Found {len(files)} files to validate")

            if len(files) == 0:
                run.status = RunStatus.COMPLETED
                run.completed_at = datetime.utcnow()
                job.last_run_at = run.started_at
                job.last_run_status = "success"
                job.total_runs += 1
                await db.commit()
                return

            # Initialize validators
            xrechnung_validator = XRechnungValidator()
            zugferd_validator = ZUGFeRDValidator()
            history_service = ValidationHistoryService(db)

            # Validate each file
            for file_info in files:
                file_record = ScheduledValidationFile(
                    run_id=run.id,
                    file_key=file_info["key"],
                    file_name=file_info["name"],
                    file_size_bytes=file_info["size"],
                )
                db.add(file_record)

                try:
                    # Download file
                    content = await client.download_file(
                        job.bucket_name, file_info["key"]
                    )
                    logger.debug(
                        f"Downloaded {file_info['name']} ({len(content)} bytes)"
                    )

                    # Determine file type and validate
                    is_pdf = file_info["name"].lower().endswith(".pdf")
                    if is_pdf:
                        validation_result = await zugferd_validator.validate(
                            content, file_info["name"], job.user_id
                        )
                    else:
                        validation_result = await xrechnung_validator.validate(
                            content, file_info["name"], job.user_id
                        )

                    # Store validation result
                    log = await history_service.store_validation(
                        result=validation_result,
                        user_id=job.user_id,
                        client_id=None,
                        file_name=file_info["name"],
                        file_size_bytes=file_info["size"],
                    )

                    file_record.is_valid = validation_result.is_valid
                    file_record.error_count = validation_result.error_count
                    file_record.warning_count = validation_result.warning_count
                    file_record.validation_log_id = log.id

                    run.files_validated += 1
                    if validation_result.is_valid:
                        run.files_valid += 1
                    else:
                        run.files_invalid += 1

                    # Post-validation actions
                    if job.move_to_folder:
                        new_key = f"{job.move_to_folder.rstrip('/')}/{file_info['name']}"
                        await client.move_file(
                            job.bucket_name, file_info["key"], new_key
                        )
                        logger.info(f"Moved {file_info['key']} to {new_key}")
                    elif job.delete_after_validation:
                        await client.delete_file(job.bucket_name, file_info["key"])
                        logger.info(f"Deleted {file_info['key']}")

                except Exception as e:
                    logger.error(f"Failed to validate {file_info['key']}: {e}")
                    file_record.error_message = str(e)
                    run.files_failed += 1

            # Update run status
            run.status = RunStatus.COMPLETED
            run.completed_at = datetime.utcnow()

            # Update job stats
            job.last_run_at = run.started_at
            job.last_run_status = "success"
            job.total_runs += 1
            job.total_files_validated += run.files_validated
            job.total_files_valid += run.files_valid
            job.total_files_invalid += run.files_invalid
            job.status = JobStatus.ACTIVE

            logger.info(
                f"Job {job_id} completed: {run.files_validated} validated, "
                f"{run.files_valid} valid, {run.files_invalid} invalid, "
                f"{run.files_failed} failed"
            )

        except Exception as e:
            logger.error(f"Scheduled validation job {job_id} failed: {e}")
            run.status = RunStatus.FAILED
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            job.last_run_status = "error"
            job.status = JobStatus.ERROR

        await db.commit()
