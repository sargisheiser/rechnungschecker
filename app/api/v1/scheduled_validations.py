"""API endpoints for scheduled validation jobs."""

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DbSession
from app.models.user import User
from app.schemas.scheduled_validation import (
    ScheduledValidationFileResponse,
    ScheduledValidationJobCreate,
    ScheduledValidationJobResponse,
    ScheduledValidationJobUpdate,
    ScheduledValidationRunResponse,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.services.scheduled_validation.service import (
    ScheduledValidationService,
    run_scheduled_validation_job,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def require_pro_plan(user: User) -> None:
    """Check if user has PRO or higher plan."""
    if not user.can_use_webhooks():  # Same permission level as webhooks
        raise HTTPException(
            status_code=403,
            detail="Scheduled validations require Pro plan or higher",
        )


@router.post("/", response_model=ScheduledValidationJobResponse)
async def create_scheduled_job(
    data: ScheduledValidationJobCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Create a new scheduled validation job.

    Requires Pro plan or higher.
    """
    require_pro_plan(current_user)

    service = ScheduledValidationService(db)

    # Test connection first
    success, message = await service.test_connection(
        provider=data.provider,
        credentials=data.credentials,
        bucket_name=data.bucket_name,
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)

    job = await service.create_job(current_user.id, data)
    await db.commit()
    await db.refresh(job)

    logger.info(f"User {current_user.id} created scheduled job {job.id}")
    return job


@router.get("/", response_model=list[ScheduledValidationJobResponse])
async def list_scheduled_jobs(
    db: DbSession,
    current_user: CurrentUser,
):
    """List all scheduled validation jobs for the current user."""
    service = ScheduledValidationService(db)
    return await service.get_user_jobs(current_user.id)


@router.get("/{job_id}", response_model=ScheduledValidationJobResponse)
async def get_scheduled_job(
    job_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    """Get a specific scheduled validation job."""
    service = ScheduledValidationService(db)
    job = await service.get_job(job_id, current_user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/{job_id}", response_model=ScheduledValidationJobResponse)
async def update_scheduled_job(
    job_id: UUID,
    data: ScheduledValidationJobUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Update a scheduled validation job."""
    service = ScheduledValidationService(db)
    job = await service.get_job(job_id, current_user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job = await service.update_job(job, **data.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(job)

    logger.info(f"User {current_user.id} updated scheduled job {job_id}")
    return job


@router.delete("/{job_id}")
async def delete_scheduled_job(
    job_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    """Delete a scheduled validation job."""
    service = ScheduledValidationService(db)
    job = await service.get_job(job_id, current_user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await service.delete_job(job)
    await db.commit()

    logger.info(f"User {current_user.id} deleted scheduled job {job_id}")
    return {"status": "deleted"}


@router.post("/{job_id}/run")
async def trigger_manual_run(
    job_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    """Manually trigger a scheduled validation job to run now."""
    service = ScheduledValidationService(db)
    job = await service.get_job(job_id, current_user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.is_enabled:
        raise HTTPException(status_code=400, detail="Job is disabled")

    # Run immediately in background
    asyncio.create_task(run_scheduled_validation_job(job_id))

    logger.info(f"User {current_user.id} manually triggered job {job_id}")
    return {"status": "started", "message": "Job triggered manually"}


@router.get("/{job_id}/runs", response_model=list[ScheduledValidationRunResponse])
async def get_job_runs(
    job_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    limit: int = 20,
):
    """Get run history for a scheduled validation job."""
    service = ScheduledValidationService(db)
    job = await service.get_job(job_id, current_user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return await service.get_job_runs(job_id, limit=min(limit, 100))


@router.get("/runs/{run_id}/files", response_model=list[ScheduledValidationFileResponse])
async def get_run_files(
    run_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    """Get files processed in a scheduled validation run."""
    service = ScheduledValidationService(db)
    files = await service.get_run_files(run_id)

    # Verify user has access to this run by checking the job
    if files:
        from sqlalchemy import select

        from app.models.scheduled_validation import ScheduledValidationRun

        result = await db.execute(
            select(ScheduledValidationRun)
            .where(ScheduledValidationRun.id == run_id)
        )
        run = result.scalar_one_or_none()
        if run:
            job = await service.get_job(run.job_id, current_user.id)
            if not job:
                raise HTTPException(status_code=404, detail="Run not found")

    return files


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_cloud_connection(
    data: TestConnectionRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Test cloud storage connection with provided credentials."""
    require_pro_plan(current_user)

    service = ScheduledValidationService(db)
    success, message = await service.test_connection(
        provider=data.provider,
        credentials=data.credentials,
        bucket_name=data.bucket_name,
    )

    return TestConnectionResponse(success=success, message=message)
