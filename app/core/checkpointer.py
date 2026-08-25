from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import get_settings

settings = get_settings()

_pool: AsyncConnectionPool | None = None
_checkpointer: AsyncPostgresSaver | None = None

async def init_checkpointer() -> AsyncPostgresSaver | None:
    global _pool, _checkpointer

    database_url = settings.database_url
    if not database_url:
        _pool = None
        _checkpointer = None
        return None

    _pool = AsyncConnectionPool(
        conninfo=database_url,
        max_size=5,
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=False,
    )

    await _pool.open()

    _checkpointer = AsyncPostgresSaver(_pool)
    await _checkpointer.setup()
    await _setup_tavily_cache_table()

    return _checkpointer

async def close_checkpointer():
    if _pool:
        await _pool.close()
        _pool = None
    _checkpointer = None


def get_checkpointer() -> AsyncPostgresSaver:
    if _checkpointer is None:
        raise RuntimeError("Checkpointer not initialized — call init_checkpointer() in lifespan first")
    return _checkpointer


def _get_pool() -> AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("Connection pool not initialized — call init_checkpointer() in lifespan first")
    return _pool


async def _setup_tavily_cache_table() -> None:
    if _pool is None:
        return

    async with _pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tavily_search_cache (
                    query TEXT NOT NULL,
                    max_results INTEGER NOT NULL,
                    result JSONB NOT NULL,
                    cached_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (query, max_results)
                )
                """
            )


async def get_tavily_cache(query: str, max_results: int, ttl_seconds: int) -> list | None:
    if _pool is None:
        return None

    async with _pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT result, EXTRACT(EPOCH FROM (NOW() - cached_at))
                FROM tavily_search_cache
                WHERE query = %s AND max_results = %s
                """,
                (query, max_results),
            )
            row = await cur.fetchone()

            if row is None:
                return None

            result, age_seconds = row
            if float(age_seconds) <= ttl_seconds:
                return result

            await cur.execute(
                "DELETE FROM tavily_search_cache WHERE query = %s AND max_results = %s",
                (query, max_results),
            )

            return None


async def set_tavily_cache(query: str, max_results: int, result: list) -> None:
    if _pool is None:
        return

    async with _pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO tavily_search_cache (query, max_results, result, cached_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (query, max_results)
                DO UPDATE SET
                    result = EXCLUDED.result,
                    cached_at = NOW()
                """,
                (query, max_results, result),
            )


async def count_tavily_cache_entries() -> int:
    if _pool is None:
        return 0

    async with _pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM tavily_search_cache")
            row = await cur.fetchone()

            if row is None:
                return 0

            return int(row[0])