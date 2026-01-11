"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import validate

api_router = APIRouter()

# Include sub-routers
api_router.include_router(validate.router, prefix="/validate", tags=["Validation"])
