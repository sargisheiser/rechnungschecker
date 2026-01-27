"""Batch validation API endpoints."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)

from app.api.deps import CurrentUser, DbSession
from app.config import get_settings
from app.models.audit import AuditAction
from app.models.batch import BatchFileStatus
from app.schemas.batch import (
    BatchJobCreated,
    BatchJobList,
    BatchJobWithFiles,
    BatchResultsSummary,
)
from app.services.audit import AuditService
from app.services.batch import BatchService

logger = logging.getLogger(__name__)
router = APIRouter()

# Maximum files per batch
MAX_FILES_PER_BATCH = 50


async def process_batch_job(job_id: UUID, user_id: UUID, client_id: UUID | None) -> None:
    """Background task to process a batch validation job."""
    from app.core.database import async_session_maker
    from app.services.validation_history import ValidationHistoryService
    from app.services.validator import XRechnungValidator, ZUGFeRDValidator

    async with async_session_maker() as db:
        try:
            batch_service = BatchService(db)
            xrechnung_validator = XRechnungValidator()
            zugferd_validator = ZUGFeRDValidator()

            # Get the job
            job = await batch_service.get_job(job_id, user_id)
            if not job:
                logger.error(f"Batch job not found: {job_id}")
                return

            # Mark job as processing
            job.start_processing()
            await db.commit()

            # Process each pending file
            pending_files = await batch_service.get_pending_files(job_id)

            for batch_file in pending_files:
                try:
                    # Mark file as processing
                    batch_file.mark_processing()
                    await db.commit()

                    content = batch_file.file_content
                    filename = batch_file.filename

                    if not content:
                        await batch_service.update_file_status(
                            batch_file.id,
                            BatchFileStatus.FAILED,
                            error_message="File content not available",
                        )
                        await batch_service.update_job_progress(job_id, successful=False)
                        await db.commit()
                        continue

                    # Determine file type and validate
                    is_pdf = filename.lower().endswith(".pdf")
                    is_xml = filename.lower().endswith(".xml")

                    if not is_pdf and not is_xml:
                        await batch_service.update_file_status(
                            batch_file.id,
                            BatchFileStatus.SKIPPED,
                            error_message="Unsupported file type",
                        )
                        await batch_service.update_job_progress(job_id, successful=False)
                        await db.commit()
                        continue

                    # Validate the file
                    if is_pdf:
                        result = await zugferd_validator.validate(
                            content=content,
                            filename=filename,
                            user_id=user_id,
                        )
                    else:
                        result = await xrechnung_validator.validate(
                            content=content,
                            filename=filename,
                            user_id=user_id,
                        )

                    # Store validation result
                    history_service = ValidationHistoryService(db)
                    log_entry = await history_service.store_validation(
                        result=result,
                        user_id=user_id,
                        client_id=client_id,
                        file_name=filename,
                        file_size_bytes=batch_file.file_size_bytes,
                    )

                    # Update file status
                    await batch_service.update_file_status(
                        batch_file.id,
                        BatchFileStatus.COMPLETED,
                        validation_id=log_entry.id,
                    )
                    await batch_service.update_job_progress(job_id, successful=True)
                    await db.commit()

                except Exception as e:
                    logger.exception(f"Error processing batch file {batch_file.id}: {e}")
                    await batch_service.update_file_status(
                        batch_file.id,
                        BatchFileStatus.FAILED,
                        error_message=str(e),
                    )
                    await batch_service.update_job_progress(job_id, successful=False)
                    await db.commit()

            # Mark job as completed (if not already)
            job = await batch_service.get_job(job_id, user_id)
            if job and not job.is_complete:
                job.mark_completed()
                await db.commit()

            logger.info(f"Batch job completed: {job_id}")

        except Exception as e:
            logger.exception(f"Error processing batch job {job_id}: {e}")
            # Try to mark job as failed
            try:
                result = await db.execute(
                    "UPDATE batch_jobs SET status = 'failed', error_message = %s WHERE id = %s",
                    (str(e), str(job_id)),
                )
                await db.commit()
            except Exception as cleanup_err:
                logger.warning(f"Failed to mark batch job {job_id} as failed: {cleanup_err}")


@router.post("/validate", response_model=BatchJobCreated)
async def create_batch_validation(
    db: DbSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    request: Request,
    files: Annotated[list[UploadFile], File(description="Invoice files to validate")],
    name: Annotated[str, Form()] = "Batch Validation",
    client_id: Annotated[UUID | None, Form()] = None,
) -> BatchJobCreated:
    """Create a new batch validation job.

    Upload multiple files for validation. Files are processed in the background.
    """
    audit_service = AuditService(db)

    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided",
        )

    if len(files) > MAX_FILES_PER_BATCH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_FILES_PER_BATCH} files per batch",
        )

    # Validate file sizes and read content
    file_data: list[tuple[str, bytes, int]] = []
    for file in files:
        content = await file.read()
        size = len(content)

        if size > get_settings().max_upload_size_bytes:
            max_size = get_settings().max_upload_size_mb
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File {file.filename} exceeds maximum size of {max_size}MB",
            )

        # Check file extension
        filename = file.filename or "unknown"
        if not filename.lower().endswith((".xml", ".pdf")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {filename} has unsupported format. "
                "Only XML and PDF files are accepted.",
            )

        file_data.append((filename, content, size))

    # Create batch job
    batch_service = BatchService(db)
    job = await batch_service.create_job(
        user_id=current_user.id,
        name=name,
        files=file_data,
        client_id=client_id,
    )

    await db.commit()

    # Log audit event
    await audit_service.log(
        user_id=current_user.id,
        action=AuditAction.VALIDATE_BATCH,
        resource_type="batch_job",
        resource_id=str(job.id),
        request=request,
        details={"name": job.name, "total_files": job.total_files},
    )

    # Start background processing
    background_tasks.add_task(
        process_batch_job,
        job.id,
        current_user.id,
        client_id,
    )

    return BatchJobCreated(
        id=job.id,
        name=job.name,
        total_files=job.total_files,
        status=job.status,
        message=f"Batch job created with {job.total_files} files. Processing started.",
    )


@router.get("/jobs", response_model=BatchJobList)
async def list_batch_jobs(
    db: DbSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
) -> BatchJobList:
    """List user's batch validation jobs."""
    batch_service = BatchService(db)
    return await batch_service.get_user_jobs(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get("/jobs/{job_id}", response_model=BatchJobWithFiles)
async def get_batch_job(
    db: DbSession,
    current_user: CurrentUser,
    job_id: UUID,
) -> BatchJobWithFiles:
    """Get batch job details including file status."""
    batch_service = BatchService(db)
    job = await batch_service.get_job_with_files(job_id, current_user.id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found",
        )

    return job


@router.get("/jobs/{job_id}/results", response_model=BatchResultsSummary)
async def get_batch_results(
    db: DbSession,
    current_user: CurrentUser,
    job_id: UUID,
) -> BatchResultsSummary:
    """Get validation results summary for a batch job."""
    batch_service = BatchService(db)
    results = await batch_service.get_results_summary(job_id, current_user.id)

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found",
        )

    return results


@router.post("/jobs/{job_id}/cancel")
async def cancel_batch_job(
    db: DbSession,
    current_user: CurrentUser,
    job_id: UUID,
) -> dict:
    """Cancel a running batch job."""
    batch_service = BatchService(db)
    success = await batch_service.cancel_job(job_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel job. Job not found or already completed.",
        )

    await db.commit()
    return {"message": "Job cancelled successfully"}


@router.delete("/jobs/{job_id}")
async def delete_batch_job(
    db: DbSession,
    current_user: CurrentUser,
    job_id: UUID,
) -> dict:
    """Delete a batch job and its files."""
    batch_service = BatchService(db)
    success = await batch_service.delete_job(job_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found",
        )

    await db.commit()
    return {"message": "Job deleted successfully"}
