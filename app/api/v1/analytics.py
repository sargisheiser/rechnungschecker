"""Analytics API endpoints for validation statistics and trends."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.services.analytics import AnalyticsService

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_analytics(
    db: DbSession,
    current_user: CurrentUser,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
    client_id: Optional[UUID] = Query(default=None, description="Filter by client ID"),
) -> dict:
    """Get comprehensive analytics for the dashboard.

    Returns:
        - period: Date range information
        - summary: Total validations, valid/invalid counts, success rate
        - by_type: Breakdown by XRechnung vs ZUGFeRD
        - by_day: Daily validation counts for charting
        - top_errors: Files with most validation errors
        - usage: Current month usage vs limits
    """
    service = AnalyticsService(db)
    return await service.get_dashboard_analytics(
        user_id=current_user.id,
        days=days,
        client_id=client_id,
    )


@router.get("/clients")
async def get_client_comparison(
    db: DbSession,
    current_user: CurrentUser,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
) -> list[dict]:
    """Get validation statistics per client for comparison.

    Only available for Steuerberater plan users.

    Returns:
        List of client statistics with validation counts and success rates
    """
    from app.models.user import SubscriptionPlan

    if current_user.plan != SubscriptionPlan.STEUERBERATER:
        return []

    service = AnalyticsService(db)
    return await service.get_client_comparison(
        user_id=current_user.id,
        days=days,
    )
