"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import auth, reports, validate

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(validate.router, prefix="/validate", tags=["Validation"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
