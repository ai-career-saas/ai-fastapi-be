from app.core.config import get_settings
from app.core.checkpointer import get_tavily_cache, set_tavily_cache
from app.core.logging import get_logger
from app.tools.search_tool import CareerSearchTool

settings = get_settings()
logger = get_logger(__name__)


def _normalize_cache_query(query: str) -> str:
    return " ".join(query.strip().lower().split())


async def search_cached(tool: CareerSearchTool, query: str, max_results: int = 5) -> list:
    cache_query = _normalize_cache_query(query)
    cached = await get_tavily_cache(
        query=cache_query,
        max_results=max_results,
        ttl_seconds=settings.cache_ttl_seconds,
    )
    if cached is not None:
        logger.info("Cache HIT: %s", query[:50])

        return cached

    logger.info("Cache MISS: %s", query[:50])
    result = await tool.search(query, max_results)
    await set_tavily_cache(query=cache_query, max_results=max_results, result=result)
    return result
