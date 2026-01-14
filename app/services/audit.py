"""Audit logging service for tracking user actions."""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditAction, AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for managing audit logs."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def log(
        self,
        user_id: UUID,
        action: AuditAction,
        resource_type: str,
        resource_id: str | None = None,
        request: Request | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        """Log an audit event.

        Args:
            user_id: The user performing the action
            action: The type of action being performed
            resource_type: The type of resource affected (e.g., "user", "client", "api_key")
            resource_id: The ID of the affected resource (optional)
            request: The FastAPI request object for extracting IP and user agent
            details: Additional context about the action (optional)

        Returns:
            The created AuditLog entry
        """
        # Extract IP address and user agent from request
        ip_address = None
        user_agent = None
        if request:
            # Handle X-Forwarded-For header for proxied requests
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                ip_address = forwarded_for.split(",")[0].strip()
            else:
                ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("User-Agent")

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )

        self.db.add(audit_log)
        await self.db.flush()

        logger.info(
            f"Audit log: user={user_id}, action={action.value}, "
            f"resource={resource_type}/{resource_id}"
        )
        return audit_log

    async def get_user_logs(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 50,
        action_filter: AuditAction | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[list[AuditLog], int]:
        """Get paginated audit logs for a user.

        Args:
            user_id: The user ID to get logs for
            page: Page number (1-indexed)
            limit: Number of items per page
            action_filter: Optional filter by action type
            date_from: Optional start date filter
            date_to: Optional end date filter

        Returns:
            Tuple of (list of AuditLog entries, total count)
        """
        offset = (page - 1) * limit

        # Build filters
        filters = [AuditLog.user_id == user_id]
        if action_filter:
            filters.append(AuditLog.action == action_filter)
        if date_from:
            filters.append(AuditLog.created_at >= date_from)
        if date_to:
            filters.append(AuditLog.created_at <= date_to)

        # Get total count
        count_query = select(func.count(AuditLog.id)).where(*filters)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get logs
        query = (
            select(AuditLog)
            .where(*filters)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        return logs, total

    async def export_user_logs(
        self,
        user_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[dict]:
        """Export all audit logs for a user (GDPR compliance).

        Args:
            user_id: The user ID to export logs for
            date_from: Optional start date filter
            date_to: Optional end date filter

        Returns:
            List of audit log dictionaries
        """
        # Build filters
        filters = [AuditLog.user_id == user_id]
        if date_from:
            filters.append(AuditLog.created_at >= date_from)
        if date_to:
            filters.append(AuditLog.created_at <= date_to)

        # Get all logs
        query = (
            select(AuditLog)
            .where(*filters)
            .order_by(AuditLog.created_at.desc())
        )
        result = await self.db.execute(query)
        logs = result.scalars().all()

        return [log.to_dict() for log in logs]

    async def get_recent_activity(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> list[AuditLog]:
        """Get recent activity for a user.

        Args:
            user_id: The user ID
            limit: Maximum number of entries to return

        Returns:
            List of recent AuditLog entries
        """
        query = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_activity_summary(
        self,
        user_id: UUID,
        days: int = 30,
    ) -> dict:
        """Get activity summary for a user.

        Args:
            user_id: The user ID
            days: Number of days to include

        Returns:
            Dictionary with activity summary
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Total actions
        total_query = select(func.count(AuditLog.id)).where(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= cutoff,
        )
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        # Actions by type
        action_counts = {}
        for action in AuditAction:
            count_query = select(func.count(AuditLog.id)).where(
                AuditLog.user_id == user_id,
                AuditLog.action == action,
                AuditLog.created_at >= cutoff,
            )
            count_result = await self.db.execute(count_query)
            count = count_result.scalar() or 0
            if count > 0:
                action_counts[action.value] = count

        return {
            "total_actions": total,
            "by_action": action_counts,
            "period_days": days,
        }
