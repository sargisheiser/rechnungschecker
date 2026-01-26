"""APScheduler-based scheduler service for cron jobs."""

import logging
from typing import Any, Callable
from uuid import UUID

from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class SchedulerService:
    """Singleton service for managing scheduled jobs using APScheduler."""

    _instance: "SchedulerService | None" = None
    _scheduler: AsyncIOScheduler | None = None

    @classmethod
    def get_instance(cls) -> "SchedulerService":
        """Get the singleton instance of the scheduler service.

        Returns:
            The singleton SchedulerService instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        """Initialize the scheduler if not already initialized."""
        if SchedulerService._scheduler is None:
            SchedulerService._scheduler = AsyncIOScheduler(
                jobstores={"default": MemoryJobStore()},
                job_defaults={
                    "coalesce": True,  # Combine missed runs into one
                    "max_instances": 1,  # Only one instance per job at a time
                    "misfire_grace_time": 60 * 5,  # 5 minutes grace for missed jobs
                },
            )
            logger.info("APScheduler initialized")

    @property
    def scheduler(self) -> AsyncIOScheduler:
        """Get the underlying APScheduler instance."""
        return SchedulerService._scheduler

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is currently running."""
        return self.scheduler.running if self.scheduler else False

    def start(self) -> None:
        """Start the scheduler if not already running."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
        else:
            logger.debug("Scheduler already running")

    def shutdown(self, wait: bool = False) -> None:
        """Shutdown the scheduler.

        Args:
            wait: If True, wait for running jobs to complete
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("Scheduler shutdown")
        else:
            logger.debug("Scheduler not running, nothing to shutdown")

    def add_job(
        self,
        job_id: UUID,
        cron_expression: str,
        timezone: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Add or replace a scheduled job.

        Args:
            job_id: Unique identifier for the job
            cron_expression: Cron expression (e.g., "0 8 * * *" for daily at 8am)
            timezone: Timezone for the cron schedule (e.g., "Europe/Berlin")
            func: The async function to call when job runs
            args: Positional arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
        """
        job_id_str = str(job_id)

        # Remove existing job if present
        existing = self.scheduler.get_job(job_id_str)
        if existing:
            self.scheduler.remove_job(job_id_str)
            logger.debug(f"Removed existing job {job_id_str} for replacement")

        # Parse cron expression and create trigger
        try:
            trigger = CronTrigger.from_crontab(cron_expression, timezone=timezone)
        except ValueError as e:
            logger.error(f"Invalid cron expression '{cron_expression}': {e}")
            raise ValueError(f"Invalid cron expression: {cron_expression}") from e

        # Add the new job
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id_str,
            args=args,
            kwargs=kwargs or {},
            replace_existing=True,
        )
        logger.info(
            f"Added scheduled job {job_id_str} with cron '{cron_expression}' "
            f"(timezone: {timezone})"
        )

    def remove_job(self, job_id: UUID) -> bool:
        """Remove a scheduled job.

        Args:
            job_id: The job ID to remove

        Returns:
            True if job was removed, False if it didn't exist
        """
        job_id_str = str(job_id)
        if self.scheduler.get_job(job_id_str):
            self.scheduler.remove_job(job_id_str)
            logger.info(f"Removed scheduled job {job_id_str}")
            return True
        else:
            logger.debug(f"Job {job_id_str} not found, nothing to remove")
            return False

    def pause_job(self, job_id: UUID) -> None:
        """Pause a scheduled job.

        Args:
            job_id: The job ID to pause
        """
        job_id_str = str(job_id)
        self.scheduler.pause_job(job_id_str)
        logger.info(f"Paused scheduled job {job_id_str}")

    def resume_job(self, job_id: UUID) -> None:
        """Resume a paused job.

        Args:
            job_id: The job ID to resume
        """
        job_id_str = str(job_id)
        self.scheduler.resume_job(job_id_str)
        logger.info(f"Resumed scheduled job {job_id_str}")

    def get_job_next_run(self, job_id: UUID) -> str | None:
        """Get the next scheduled run time for a job.

        Args:
            job_id: The job ID to check

        Returns:
            ISO format datetime string or None if job doesn't exist
        """
        job_id_str = str(job_id)
        job = self.scheduler.get_job(job_id_str)
        if job and job.next_run_time:
            return job.next_run_time.isoformat()
        return None

    def get_all_jobs(self) -> list[dict]:
        """Get information about all scheduled jobs.

        Returns:
            List of dicts with job_id, next_run_time, and pending status
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "job_id": job.id,
                    "next_run_time": (
                        job.next_run_time.isoformat() if job.next_run_time else None
                    ),
                    "pending": job.pending,
                }
            )
        return jobs
