"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import select

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.database import async_session_maker, close_db, init_db
from app.models.scheduled_validation import ScheduledValidationJob
from app.services.scheduled_validation.service import run_scheduled_validation_job
from app.services.scheduler.service import SchedulerService

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info("Starting RechnungsChecker API...")
    await init_db()
    logger.info("Database initialized")

    # Start the scheduler
    scheduler = SchedulerService.get_instance()
    scheduler.start()
    logger.info("Scheduler started")

    # Load existing scheduled validation jobs from database
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(ScheduledValidationJob).where(
                    ScheduledValidationJob.is_enabled == True  # noqa: E712
                )
            )
            jobs = result.scalars().all()
            for job in jobs:
                scheduler.add_job(
                    job_id=job.id,
                    cron_expression=job.schedule_cron,
                    timezone=job.timezone,
                    func=run_scheduled_validation_job,
                    args=(job.id,),
                )
            logger.info(f"Loaded {len(jobs)} scheduled validation jobs")
    except Exception as e:
        logger.error(f"Failed to load scheduled jobs: {e}")

    yield

    # Shutdown
    logger.info("Shutting down RechnungsChecker API...")

    # Shutdown the scheduler
    scheduler = SchedulerService.get_instance()
    scheduler.shutdown()
    logger.info("Scheduler stopped")

    await close_db()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="E-Invoice Validation & Conversion Platform for German SMEs",
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
        openapi_url="/api/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "version": settings.app_version}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
