"""Analytics service for validation statistics and trends."""

import logging
from datetime import datetime, date, timedelta
from uuid import UUID

from sqlalchemy import select, func, case, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.validation import FileType, ValidationLog
from app.models.user import User

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics and reporting."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def get_dashboard_analytics(
        self,
        user_id: UUID,
        days: int = 30,
        client_id: UUID | None = None,
    ) -> dict:
        """Get comprehensive analytics for the dashboard.

        Args:
            user_id: User ID to get analytics for
            days: Number of days to include (default 30)
            client_id: Optional client ID to filter by

        Returns:
            Dictionary with all analytics data
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # Build base filters
        filters = [
            ValidationLog.user_id == user_id,
            ValidationLog.created_at >= cutoff,
        ]
        if client_id:
            filters.append(ValidationLog.client_id == client_id)

        # Get summary statistics
        summary = await self._get_summary_stats(filters)

        # Get by type breakdown
        by_type = await self._get_by_type_stats(filters)

        # Get daily breakdown
        by_day = await self._get_daily_stats(user_id, start_date, end_date, client_id)

        # Get top errors
        top_errors = await self._get_top_errors(filters)

        # Get user usage info
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        usage = {}
        if user:
            usage = {
                "validations_used": user.validations_this_month,
                "validations_limit": user.get_validation_limit(),
                "conversions_used": user.conversions_this_month,
                "conversions_limit": user.get_conversion_limit(),
                "plan": user.plan.value,
            }

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            "summary": summary,
            "by_type": by_type,
            "by_day": by_day,
            "top_errors": top_errors,
            "usage": usage,
        }

    async def _get_summary_stats(self, filters: list) -> dict:
        """Get summary statistics."""
        # Total validations
        total_query = select(func.count(ValidationLog.id)).where(*filters)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        # Valid count
        valid_query = select(func.count(ValidationLog.id)).where(
            *filters,
            ValidationLog.is_valid == True,  # noqa: E712
        )
        valid_result = await self.db.execute(valid_query)
        valid = valid_result.scalar() or 0

        # Average processing time
        avg_time_query = select(func.avg(ValidationLog.processing_time_ms)).where(*filters)
        avg_time_result = await self.db.execute(avg_time_query)
        avg_time = avg_time_result.scalar() or 0

        # Total errors and warnings
        error_query = select(func.sum(ValidationLog.error_count)).where(*filters)
        error_result = await self.db.execute(error_query)
        total_errors = error_result.scalar() or 0

        warning_query = select(func.sum(ValidationLog.warning_count)).where(*filters)
        warning_result = await self.db.execute(warning_query)
        total_warnings = warning_result.scalar() or 0

        return {
            "total_validations": total,
            "valid_count": valid,
            "invalid_count": total - valid,
            "success_rate": round(valid / total * 100, 1) if total > 0 else 0,
            "avg_processing_time_ms": round(avg_time, 0),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
        }

    async def _get_by_type_stats(self, filters: list) -> dict:
        """Get breakdown by file type."""
        # XRechnung count
        xrechnung_query = select(func.count(ValidationLog.id)).where(
            *filters,
            ValidationLog.file_type == FileType.XRECHNUNG,
        )
        xrechnung_result = await self.db.execute(xrechnung_query)
        xrechnung = xrechnung_result.scalar() or 0

        # ZUGFeRD count
        zugferd_query = select(func.count(ValidationLog.id)).where(
            *filters,
            ValidationLog.file_type == FileType.ZUGFERD,
        )
        zugferd_result = await self.db.execute(zugferd_query)
        zugferd = zugferd_result.scalar() or 0

        return {
            "xrechnung": xrechnung,
            "zugferd": zugferd,
        }

    async def _get_daily_stats(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
        client_id: UUID | None = None,
    ) -> list[dict]:
        """Get validation counts per day."""
        # Build filters
        filters = [
            ValidationLog.user_id == user_id,
            cast(ValidationLog.created_at, Date) >= start_date,
            cast(ValidationLog.created_at, Date) <= end_date,
        ]
        if client_id:
            filters.append(ValidationLog.client_id == client_id)

        # Query with daily grouping
        query = (
            select(
                cast(ValidationLog.created_at, Date).label("date"),
                func.count(ValidationLog.id).label("total"),
                func.sum(
                    case((ValidationLog.is_valid == True, 1), else_=0)  # noqa: E712
                ).label("valid"),
                func.sum(
                    case((ValidationLog.is_valid == False, 1), else_=0)  # noqa: E712
                ).label("invalid"),
            )
            .where(*filters)
            .group_by(cast(ValidationLog.created_at, Date))
            .order_by(cast(ValidationLog.created_at, Date))
        )

        result = await self.db.execute(query)
        rows = result.all()

        # Convert to list of dicts with all dates filled in
        daily_data = {row.date: {"valid": row.valid or 0, "invalid": row.invalid or 0} for row in rows}

        # Fill in missing dates with zeros
        all_days = []
        current = start_date
        while current <= end_date:
            data = daily_data.get(current, {"valid": 0, "invalid": 0})
            all_days.append({
                "date": current.isoformat(),
                "valid": data["valid"],
                "invalid": data["invalid"],
            })
            current += timedelta(days=1)

        return all_days

    async def _get_top_errors(self, filters: list, limit: int = 5) -> list[dict]:
        """Get most common validation errors.

        Note: This is a simplified version that returns error counts per validation.
        A full implementation would require storing individual error messages.
        """
        # For now, return validations with highest error counts
        query = (
            select(
                ValidationLog.file_name,
                ValidationLog.error_count,
                ValidationLog.warning_count,
                ValidationLog.file_type,
            )
            .where(*filters, ValidationLog.error_count > 0)
            .order_by(ValidationLog.error_count.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "file_name": row.file_name or "Unknown",
                "error_count": row.error_count,
                "warning_count": row.warning_count,
                "file_type": row.file_type.value,
            }
            for row in rows
        ]

    async def get_client_comparison(
        self,
        user_id: UUID,
        days: int = 30,
    ) -> list[dict]:
        """Get validation statistics per client for comparison.

        Args:
            user_id: User ID (must be Steuerberater plan)
            days: Number of days to include

        Returns:
            List of client statistics
        """
        from app.models.client import Client

        cutoff = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                Client.id,
                Client.name,
                func.count(ValidationLog.id).label("total"),
                func.sum(
                    case((ValidationLog.is_valid == True, 1), else_=0)  # noqa: E712
                ).label("valid"),
            )
            .join(ValidationLog, ValidationLog.client_id == Client.id, isouter=True)
            .where(
                Client.user_id == user_id,
                (ValidationLog.created_at >= cutoff) | (ValidationLog.created_at.is_(None)),
            )
            .group_by(Client.id, Client.name)
            .order_by(func.count(ValidationLog.id).desc())
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "client_id": str(row.id),
                "client_name": row.name,
                "total_validations": row.total or 0,
                "valid_count": row.valid or 0,
                "invalid_count": (row.total or 0) - (row.valid or 0),
                "success_rate": round((row.valid or 0) / row.total * 100, 1) if row.total else 0,
            }
            for row in rows
        ]
