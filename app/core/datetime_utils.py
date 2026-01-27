"""Datetime utilities for timezone-aware UTC handling."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Get current UTC time as a naive datetime.

    Returns a timezone-naive datetime in UTC, compatible with
    PostgreSQL TIMESTAMP WITHOUT TIME ZONE columns.

    This replaces datetime.utcnow() which is deprecated in Python 3.12+.

    Returns:
        Naive datetime representing current UTC time
    """
    return datetime.now(UTC).replace(tzinfo=None)
