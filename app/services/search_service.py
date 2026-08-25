from app.services.cache_service import search_cached
from app.tools.search_tool import CareerSearchTool


async def search(query: str, max_results: int = 5) -> list:
    tool = CareerSearchTool()
    return await search_cached(tool, query, max_results)
