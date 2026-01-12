"""Simple in-memory cache for validation results."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID

from app.schemas.validation import ValidationResponse

logger = logging.getLogger(__name__)

# Simple in-memory cache with expiration
_validation_cache: Dict[str, tuple[ValidationResponse, datetime]] = {}
CACHE_EXPIRY_MINUTES = 30


def cache_validation_result(result: ValidationResponse) -> None:
    """Cache a validation result for later PDF generation.

    Args:
        result: ValidationResponse to cache
    """
    key = str(result.id)
    _validation_cache[key] = (result, datetime.utcnow())
    logger.debug(f"Cached validation result: {key}")

    # Clean up expired entries
    _cleanup_expired()


def get_cached_validation(validation_id: str | UUID) -> Optional[ValidationResponse]:
    """Retrieve a cached validation result.

    Args:
        validation_id: UUID of the validation

    Returns:
        ValidationResponse if found and not expired, None otherwise
    """
    key = str(validation_id)
    entry = _validation_cache.get(key)

    if entry is None:
        return None

    result, cached_at = entry
    if datetime.utcnow() - cached_at > timedelta(minutes=CACHE_EXPIRY_MINUTES):
        # Expired
        del _validation_cache[key]
        return None

    return result


def _cleanup_expired() -> None:
    """Remove expired entries from cache."""
    now = datetime.utcnow()
    expired_keys = [
        key for key, (_, cached_at) in _validation_cache.items()
        if now - cached_at > timedelta(minutes=CACHE_EXPIRY_MINUTES)
    ]
    for key in expired_keys:
        del _validation_cache[key]

    if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
