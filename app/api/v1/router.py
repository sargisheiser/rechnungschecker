"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import api_keys, auth, billing, convert, reports, validate

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(validate.router, prefix="/validate", tags=["Validation"])
api_router.include_router(convert.router, prefix="/convert", tags=["Conversion"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])
