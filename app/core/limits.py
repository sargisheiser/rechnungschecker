"""Rate limiting and usage tracking."""

import hashlib
import logging
from datetime import date, datetime
from uuid import uuid4

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import RateLimitError, UsageLimitError
from app.models.user import GuestUsage, User

logger = logging.getLogger(__name__)
settings = get_settings()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check for forwarded headers (reverse proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain (original client)
        return forwarded.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct client
    if request.client:
        return request.client.host

    return "unknown"


def get_guest_cookie_id(request: Request) -> str | None:
    """Get guest tracking cookie ID from request."""
    return request.cookies.get("guest_id")


def generate_guest_cookie_id() -> str:
    """Generate a new guest tracking cookie ID."""
    return hashlib.sha256(uuid4().bytes).hexdigest()[:32]


async def get_or_create_guest_usage(
    db: AsyncSession,
    ip_address: str,
    cookie_id: str | None = None,
) -> GuestUsage:
    """Get or create guest usage record.

    Args:
        db: Database session
        ip_address: Client IP address
        cookie_id: Optional guest cookie ID

    Returns:
        GuestUsage record
    """
    # Try to find existing record by IP or cookie
    query = select(GuestUsage).where(GuestUsage.ip_address == ip_address)
    if cookie_id:
        query = query.where(
            (GuestUsage.ip_address == ip_address) | (GuestUsage.cookie_id == cookie_id)
        )

    result = await db.execute(query)
    guest = result.scalar_one_or_none()

    if guest is None:
        # Create new guest record
        guest = GuestUsage(
            ip_address=ip_address,
            cookie_id=cookie_id,
            validations_used=0,
        )
        db.add(guest)
        await db.flush()
        logger.debug(f"Created new guest usage record for IP: {ip_address}")

    return guest


async def check_guest_limit(
    db: AsyncSession,
    request: Request,
) -> tuple[GuestUsage, str | None]:
    """Check if guest can perform validation.

    Args:
        db: Database session
        request: FastAPI request

    Returns:
        Tuple of (GuestUsage record, new_cookie_id if needed)

    Raises:
        UsageLimitError: If guest limit exceeded
    """
    ip_address = get_client_ip(request)
    cookie_id = get_guest_cookie_id(request)
    new_cookie_id = None

    # Generate cookie if not present
    if cookie_id is None:
        new_cookie_id = generate_guest_cookie_id()
        cookie_id = new_cookie_id

    guest = await get_or_create_guest_usage(db, ip_address, cookie_id)

    # Update cookie if we have a new one
    if new_cookie_id and guest.cookie_id != new_cookie_id:
        guest.cookie_id = new_cookie_id

    if not guest.can_validate(settings.guest_validations_limit):
        raise UsageLimitError(
            f"Kostenlose Validierungen aufgebraucht ({settings.guest_validations_limit}/Monat). "
            "Bitte registrieren Sie sich für mehr.",
            details={
                "limit": settings.guest_validations_limit,
                "used": guest.validations_used,
            },
        )

    return guest, new_cookie_id


async def increment_guest_usage(guest: GuestUsage) -> None:
    """Increment guest validation counter.

    Args:
        guest: GuestUsage record to update
    """
    guest.validations_used += 1
    guest.last_validation_at = datetime.utcnow()


async def check_user_validation_limit(user: User) -> None:
    """Check if user can perform validation.

    Args:
        user: User to check

    Raises:
        UsageLimitError: If user limit exceeded
    """
    # Check if usage needs reset (new month)
    today = date.today()
    if user.usage_reset_date.month != today.month or user.usage_reset_date.year != today.year:
        user.validations_this_month = 0
        user.conversions_this_month = 0
        user.usage_reset_date = today
        logger.info(f"Reset monthly usage for user: {user.email}")

    if not user.can_validate():
        limit = user.get_validation_limit()
        raise UsageLimitError(
            f"Monatliches Validierungslimit erreicht ({limit}). "
            "Bitte upgraden Sie Ihren Plan.",
            details={
                "limit": limit,
                "used": user.validations_this_month,
                "plan": user.plan.value,
            },
        )


async def check_user_conversion_limit(user: User) -> None:
    """Check if user can perform conversion.

    Args:
        user: User to check

    Raises:
        UsageLimitError: If user limit exceeded
    """
    # Check if usage needs reset (new month)
    today = date.today()
    if user.usage_reset_date.month != today.month or user.usage_reset_date.year != today.year:
        user.validations_this_month = 0
        user.conversions_this_month = 0
        user.usage_reset_date = today

    if not user.can_convert():
        limit = user.get_conversion_limit()
        raise UsageLimitError(
            f"Monatliches Konvertierungslimit erreicht ({limit}). "
            "Bitte upgraden Sie Ihren Plan.",
            details={
                "limit": limit,
                "used": user.conversions_this_month,
                "plan": user.plan.value,
            },
        )


async def increment_user_validation(user: User) -> None:
    """Increment user validation counter.

    Args:
        user: User to update
    """
    user.validations_this_month += 1


async def increment_user_conversion(user: User) -> None:
    """Increment user conversion counter.

    Args:
        user: User to update
    """
    user.conversions_this_month += 1


class RateLimiter:
    """Simple in-memory rate limiter.

    For production, use Redis-based rate limiting.
    """

    def __init__(self) -> None:
        """Initialize rate limiter with in-memory storage."""
        self._requests: dict[str, list[datetime]] = {}

    def _cleanup_old_requests(self, key: str, window_seconds: int = 60) -> None:
        """Remove requests older than the window."""
        if key not in self._requests:
            return

        cutoff = datetime.utcnow()
        self._requests[key] = [
            ts for ts in self._requests[key]
            if (cutoff - ts).total_seconds() < window_seconds
        ]

    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> bool:
        """Check if request is within rate limit.

        Args:
            key: Unique identifier (e.g., IP or user ID)
            limit: Maximum requests per window
            window_seconds: Time window in seconds

        Returns:
            True if within limit, False if exceeded
        """
        self._cleanup_old_requests(key, window_seconds)

        if key not in self._requests:
            self._requests[key] = []

        if len(self._requests[key]) >= limit:
            return False

        self._requests[key].append(datetime.utcnow())
        return True

    def get_remaining(self, key: str, limit: int) -> int:
        """Get remaining requests for a key."""
        self._cleanup_old_requests(key)
        if key not in self._requests:
            return limit
        return max(0, limit - len(self._requests[key]))


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(request: Request, is_authenticated: bool = False) -> None:
    """Check rate limit for request.

    Args:
        request: FastAPI request
        is_authenticated: Whether user is authenticated

    Raises:
        RateLimitError: If rate limit exceeded
    """
    ip = get_client_ip(request)
    limit = (
        settings.auth_rate_limit_per_minute
        if is_authenticated
        else settings.guest_rate_limit_per_minute
    )

    if not rate_limiter.check_rate_limit(ip, limit):
        raise RateLimitError(
            "Zu viele Anfragen. Bitte versuchen Sie es später erneut.",
            details={"retry_after": 60},
        )
