"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    analytics,
    api_keys,
    audit,
    auth,
    batch,
    billing,
    clients,
    convert,
    export,
    integrations,
    invoices,
    organizations,
    reports,
    scheduled_validations,
    templates,
    validate,
    webhooks,
)

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(validate.router, prefix="/validate", tags=["Validation"])
api_router.include_router(convert.router, prefix="/convert", tags=["Conversion"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])
api_router.include_router(clients.router, prefix="/clients", tags=["Clients"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(export.router, prefix="/export", tags=["Export"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["Integrations"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(batch.router, prefix="/batch", tags=["Batch"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(scheduled_validations.router, prefix="/scheduled-validations", tags=["Scheduled Validations"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
