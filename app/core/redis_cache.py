import json

import redis.asyncio as redis

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

_redis: redis.Redis | None = None

CACHE_KEY_PREFIX = "tavily_cache"
REDIS_TIMEOUT_SECONDS = 2

async def init_redis() -> redis.Redis | None:
    global _redis

    redis_url = settings.redis_url
    if not redis_url:
        _redis = None
        return None

    _redis = redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=REDIS_TIMEOUT_SECONDS,
        socket_timeout=REDIS_TIMEOUT_SECONDS,
        retry_on_timeout=False,
    )
    try:
        await _redis.ping()
    except redis.exceptions.RedisError as error:
        logger.warning("Redis unavailable; caching disabled: %s", error)
        await close_redis()
        return None

    return _redis

async def close_redis() -> None:
    global _redis

    if _redis:
        await _redis.close()
        _redis = None

def _cache_key(query: str, max_results: int) -> str:
    return f"{CACHE_KEY_PREFIX}:{max_results}:{query}"


async def get_tavily_cache(query: str, max_results: int) -> list | None:
    if _redis is None:
        return None

    try:
        raw = await _redis.get(_cache_key(query, max_results))
    except redis.exceptions.RedisError as error:
        logger.warning("Redis read failed; treating as cache miss: %s", error)
        await close_redis()
        return None

    if raw is None:
        return None

    return json.loads(raw)

async def set_tavily_cache(query: str, max_results: int, result: list, ttl_seconds: int) -> None:
    if _redis is None:
        return

    try:
        await _redis.set(
            _cache_key(query, max_results),
            json.dumps(result),
            ex=ttl_seconds,
        )
    except redis.exceptions.RedisError as error:
        logger.warning("Redis write failed; continuing without cache: %s", error)
        await close_redis()

async def count_tavily_cache_entries() -> int:
    if _redis is None:
        return 0

    try:
        count = 0
        async for _ in _redis.scan_iter(match=f"{CACHE_KEY_PREFIX}:*"):
            count += 1
    except redis.exceptions.RedisError as error:
        logger.warning("Redis count failed; reporting no cache entries: %s", error)
        await close_redis()
        return 0

    return count
