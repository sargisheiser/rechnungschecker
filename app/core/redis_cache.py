"""Redis cache utility for application-wide caching."""

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
_redis_pool: redis.ConnectionPool | None = None
_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get or create Redis client with connection pool.

    Returns:
        Async Redis client
    """
    global _redis_pool, _redis_client

    if _redis_client is None:
        settings = get_settings()
        _redis_pool = redis.ConnectionPool.from_url(
            str(settings.redis_url),
            decode_responses=True,
        )
        _redis_client = redis.Redis(connection_pool=_redis_pool)
        logger.info("Redis connection pool initialized")

    return _redis_client


async def close_redis() -> None:
    """Close Redis connection pool."""
    global _redis_pool, _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis connection pool closed")


async def cache_get(key: str) -> Any | None:
    """Get value from cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    try:
        client = await get_redis()
        value = await client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as e:
        logger.warning(f"Redis cache get failed for key {key}: {e}")
        return None


async def cache_set(
    key: str,
    value: Any,
    ttl_seconds: int = 300,
) -> bool:
    """Set value in cache with TTL.

    Args:
        key: Cache key
        value: Value to cache (must be JSON serializable)
        ttl_seconds: Time to live in seconds (default 5 minutes)

    Returns:
        True if successful
    """
    try:
        client = await get_redis()
        serialized = json.dumps(value, default=str)
        await client.setex(key, ttl_seconds, serialized)
        return True
    except Exception as e:
        logger.warning(f"Redis cache set failed for key {key}: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """Delete key from cache.

    Args:
        key: Cache key

    Returns:
        True if deleted
    """
    try:
        client = await get_redis()
        await client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Redis cache delete failed for key {key}: {e}")
        return False


async def cache_delete_pattern(pattern: str) -> int:
    """Delete all keys matching pattern.

    Args:
        pattern: Key pattern (e.g., "analytics:*")

    Returns:
        Number of keys deleted
    """
    try:
        client = await get_redis()
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await client.delete(*keys)
        return len(keys)
    except Exception as e:
        logger.warning(f"Redis cache delete pattern failed for {pattern}: {e}")
        return 0


# Cache key builders
def analytics_cache_key(user_id: str, period: str = "30d") -> str:
    """Build cache key for analytics dashboard."""
    return f"analytics:dashboard:{user_id}:{period}"


def user_cache_key(user_id: str) -> str:
    """Build cache key for user profile."""
    return f"user:profile:{user_id}"


def templates_cache_key(user_id: str) -> str:
    """Build cache key for user templates."""
    return f"templates:list:{user_id}"
