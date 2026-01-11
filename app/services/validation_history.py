"""Validation history service for storing and retrieving validation logs."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.validation import FileType, ValidationLog
from app.schemas.validation import (
    ValidationHistoryItem,
    ValidationHistoryResponse,
    ValidationResponse,
)

logger = logging.getLogger(__name__)


class ValidationHistoryService:
    """Service for managing validation history."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def store_validation(
        self,
        result: ValidationResponse,
        user_id: UUID | None = None,
    ) -> ValidationLog:
        """Store a validation result in the database.

        Args:
            result: The validation response to store
            user_id: Optional user ID who performed the validation

        Returns:
            The created ValidationLog entry
        """
        # Determine file type enum
        file_type = (
            FileType.ZUGFERD if result.file_type == "zugferd" else FileType.XRECHNUNG
        )

        log_entry = ValidationLog(
            id=result.id,
            user_id=user_id,
            file_type=file_type,
            file_hash=result.file_hash,
            file_size_bytes=0,  # We don't store the actual size for privacy
            is_valid=result.is_valid,
            error_count=result.error_count,
            warning_count=result.warning_count,
            info_count=result.info_count,
            xrechnung_version=result.xrechnung_version,
            zugferd_profile=result.zugferd_profile,
            processing_time_ms=result.processing_time_ms,
            validator_version=result.validator_version,
        )

        self.db.add(log_entry)
        await self.db.flush()

        logger.info(f"Stored validation log: id={log_entry.id}, user_id={user_id}")
        return log_entry

    async def get_user_history(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> ValidationHistoryResponse:
        """Get validation history for a user.

        Args:
            user_id: The user ID to get history for
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            ValidationHistoryResponse with paginated results
        """
        # Calculate offset
        offset = (page - 1) * page_size

        # Get total count
        count_query = select(func.count(ValidationLog.id)).where(
            ValidationLog.user_id == user_id
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get items
        query = (
            select(ValidationLog)
            .where(ValidationLog.user_id == user_id)
            .order_by(ValidationLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        logs = result.scalars().all()

        # Convert to response items
        items = [
            ValidationHistoryItem(
                id=log.id,
                file_type=log.file_type.value,
                is_valid=log.is_valid,
                error_count=log.error_count,
                warning_count=log.warning_count,
                validated_at=log.created_at,
            )
            for log in logs
        ]

        return ValidationHistoryResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_validation_by_id(
        self,
        validation_id: UUID,
        user_id: UUID | None = None,
    ) -> ValidationLog | None:
        """Get a specific validation log by ID.

        Args:
            validation_id: The validation ID to retrieve
            user_id: Optional user ID for access control

        Returns:
            ValidationLog if found and accessible, None otherwise
        """
        query = select(ValidationLog).where(ValidationLog.id == validation_id)

        # If user_id is provided, also check ownership
        if user_id is not None:
            query = query.where(ValidationLog.user_id == user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_validation_stats(
        self,
        user_id: UUID | None = None,
        days: int = 30,
    ) -> dict:
        """Get validation statistics.

        Args:
            user_id: Optional user ID to filter stats
            days: Number of days to include

        Returns:
            Dictionary with statistics
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)

        # Base query
        base_query = select(ValidationLog).where(ValidationLog.created_at >= cutoff)
        if user_id:
            base_query = base_query.where(ValidationLog.user_id == user_id)

        # Total validations
        total_query = select(func.count(ValidationLog.id)).where(
            ValidationLog.created_at >= cutoff
        )
        if user_id:
            total_query = total_query.where(ValidationLog.user_id == user_id)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        # Valid count
        valid_query = select(func.count(ValidationLog.id)).where(
            ValidationLog.created_at >= cutoff,
            ValidationLog.is_valid == True,  # noqa: E712
        )
        if user_id:
            valid_query = valid_query.where(ValidationLog.user_id == user_id)
        valid_result = await self.db.execute(valid_query)
        valid = valid_result.scalar() or 0

        # By file type
        xrechnung_query = select(func.count(ValidationLog.id)).where(
            ValidationLog.created_at >= cutoff,
            ValidationLog.file_type == FileType.XRECHNUNG,
        )
        if user_id:
            xrechnung_query = xrechnung_query.where(ValidationLog.user_id == user_id)
        xrechnung_result = await self.db.execute(xrechnung_query)
        xrechnung_count = xrechnung_result.scalar() or 0

        zugferd_query = select(func.count(ValidationLog.id)).where(
            ValidationLog.created_at >= cutoff,
            ValidationLog.file_type == FileType.ZUGFERD,
        )
        if user_id:
            zugferd_query = zugferd_query.where(ValidationLog.user_id == user_id)
        zugferd_result = await self.db.execute(zugferd_query)
        zugferd_count = zugferd_result.scalar() or 0

        return {
            "total_validations": total,
            "valid_count": valid,
            "invalid_count": total - valid,
            "valid_rate": round(valid / total * 100, 1) if total > 0 else 0,
            "by_type": {
                "xrechnung": xrechnung_count,
                "zugferd": zugferd_count,
            },
            "period_days": days,
        }
