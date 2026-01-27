"""Admin API endpoints."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import case, func, select

from app.api.deps import CurrentAdmin, DbSession
from app.models.audit import AuditLog
from app.models.user import PlanType, User
from app.models.validation import ValidationLog
from app.schemas.admin import (
    AdminAuditLogItem,
    AdminAuditLogList,
    AdminUserDetail,
    AdminUserList,
    AdminUserListItem,
    AdminUserUpdate,
    PlatformStats,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/stats",
    response_model=PlatformStats,
    summary="Get platform statistics",
    description="Get platform-wide statistics (admin only).",
)
async def get_platform_stats(
    admin: CurrentAdmin,
    db: DbSession,
) -> PlatformStats:
    """Get platform-wide statistics."""
    # Consolidated user statistics query (1 query instead of 7+)
    user_stats_query = select(
        func.count(User.id).label("total"),
        func.count(User.id).filter(User.is_active == True).label("active"),  # noqa: E712
        func.count(User.id).filter(User.is_verified == True).label("verified"),  # noqa: E712
        func.sum(User.conversions_this_month).label("conversions"),
        func.count(User.id).filter(User.plan == PlanType.FREE).label("plan_free"),
        func.count(User.id).filter(User.plan == PlanType.STARTER).label("plan_starter"),
        func.count(User.id).filter(User.plan == PlanType.PRO).label("plan_pro"),
        func.count(User.id).filter(User.plan == PlanType.STEUERBERATER).label("plan_steuerberater"),
    )
    user_stats_result = await db.execute(user_stats_query)
    user_stats = user_stats_result.one()

    total_users = user_stats.total or 0
    active_users = user_stats.active or 0
    verified_users = user_stats.verified or 0
    total_conversions = user_stats.conversions or 0

    users_by_plan = {
        PlanType.FREE.value: user_stats.plan_free or 0,
        PlanType.STARTER.value: user_stats.plan_starter or 0,
        PlanType.PRO.value: user_stats.plan_pro or 0,
        PlanType.STEUERBERATER.value: user_stats.plan_steuerberater or 0,
    }

    # Consolidated validation statistics query (1 query instead of 4)
    today_start = datetime.now(UTC).replace(tzinfo=None).replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    validation_stats_query = select(
        func.count(ValidationLog.id).label("total"),
        func.count(ValidationLog.id).filter(
            ValidationLog.created_at >= today_start
        ).label("today"),
        func.count(ValidationLog.id).filter(
            ValidationLog.created_at >= week_start
        ).label("week"),
        func.count(ValidationLog.id).filter(
            ValidationLog.created_at >= month_start
        ).label("month"),
    )
    validation_stats_result = await db.execute(validation_stats_query)
    validation_stats = validation_stats_result.one()

    total_validations = validation_stats.total or 0
    validations_today = validation_stats.today or 0
    validations_this_week = validation_stats.week or 0
    validations_this_month = validation_stats.month or 0

    # Recent registrations (last 10)
    recent_result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(10)
    )
    recent_users = recent_result.scalars().all()

    return PlatformStats(
        total_users=total_users,
        active_users=active_users,
        verified_users=verified_users,
        total_validations=total_validations,
        total_conversions=total_conversions,
        validations_today=validations_today,
        validations_this_week=validations_this_week,
        validations_this_month=validations_this_month,
        users_by_plan=users_by_plan,
        recent_registrations=[
            AdminUserListItem.model_validate(user) for user in recent_users
        ],
    )


@router.get(
    "/users",
    response_model=AdminUserList,
    summary="List all users",
    description="Get paginated list of all users (admin only).",
)
async def list_users(
    admin: CurrentAdmin,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="Search by email or name"),
    plan: str | None = Query(None, description="Filter by plan"),
    is_active: bool | None = Query(None, description="Filter by active status"),
) -> AdminUserList:
    """List all users with pagination and filtering."""
    # Base query
    query = select(User)

    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_pattern)) |
            (User.full_name.ilike(search_pattern)) |
            (User.company_name.ilike(search_pattern))
        )

    if plan:
        try:
            plan_type = PlanType(plan)
            query = query.where(User.plan == plan_type)
        except ValueError:
            pass  # Invalid plan, ignore filter

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    return AdminUserList(
        items=[AdminUserListItem.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetail,
    summary="Get user details",
    description="Get detailed information about a specific user (admin only).",
)
async def get_user(
    user_id: UUID,
    admin: CurrentAdmin,
    db: DbSession,
) -> AdminUserDetail:
    """Get detailed information about a specific user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    return AdminUserDetail.model_validate(user)


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserDetail,
    summary="Update user",
    description="Update a user's details (admin only).",
)
async def update_user(
    user_id: UUID,
    data: AdminUserUpdate,
    admin: CurrentAdmin,
    db: DbSession,
) -> AdminUserDetail:
    """Update a user's details."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    # Prevent admin from modifying their own admin status
    if user.id == admin.id and data.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sie koennen Ihren eigenen Admin-Status nicht entfernen",
        )

    # Update fields
    if data.is_active is not None:
        user.is_active = data.is_active

    if data.is_verified is not None:
        user.is_verified = data.is_verified

    if data.is_admin is not None:
        user.is_admin = data.is_admin

    if data.plan is not None:
        user.plan = PlanType(data.plan)

    if data.full_name is not None:
        user.full_name = data.full_name

    if data.company_name is not None:
        user.company_name = data.company_name

    await db.flush()
    await db.refresh(user)

    logger.info(f"Admin {admin.email} updated user {user.email}")

    return AdminUserDetail.model_validate(user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete user",
    description="Permanently delete a user account (admin only).",
)
async def delete_user(
    user_id: UUID,
    admin: CurrentAdmin,
    db: DbSession,
) -> dict[str, str]:
    """Delete a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    # Prevent admin from deleting themselves
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sie koennen Ihr eigenes Konto nicht loeschen",
        )

    email = user.email
    await db.delete(user)
    await db.flush()

    logger.info(f"Admin {admin.email} deleted user {email}")

    return {"message": f"Benutzer {email} wurde geloescht"}


@router.get(
    "/audit",
    response_model=AdminAuditLogList,
    summary="Get all audit logs",
    description="Get paginated audit logs for all users (admin only).",
)
async def get_audit_logs(
    admin: CurrentAdmin,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: UUID | None = Query(None, description="Filter by user ID"),
    action: str | None = Query(None, description="Filter by action type"),
) -> AdminAuditLogList:
    """Get paginated audit logs for all users."""
    # Base query with user join for email
    query = select(AuditLog)

    # Apply filters
    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    if action:
        query = query.where(AuditLog.action == action)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    logs = result.scalars().all()

    # Get user emails for the logs
    user_ids = {log.user_id for log in logs}
    if user_ids:
        users_result = await db.execute(
            select(User.id, User.email).where(User.id.in_(user_ids))
        )
        user_emails = {row.id: row.email for row in users_result}
    else:
        user_emails = {}

    items = []
    for log in logs:
        item = AdminAuditLogItem(
            id=log.id,
            user_id=log.user_id,
            user_email=user_emails.get(log.user_id),
            action=log.action.value if hasattr(log.action, 'value') else str(log.action),
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            details=log.details,
            created_at=log.created_at,
        )
        items.append(item)

    return AdminAuditLogList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
