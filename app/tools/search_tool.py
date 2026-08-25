import asyncio
from tavily import TavilyClient

from app.core.config import get_settings

settings = get_settings()

class CareerSearchTool:
    def __init__(self):
        self.client = TavilyClient(api_key=settings.tavily_api_key)

    # This method performs an asynchronous search using the TavilyClient inbackground thread
    # and processes the results to return a structured list of summaries and sources.
    async def search(self, query: str, max_results: int = 5) -> list[dict]:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",
                include_answer=True,
            ),
        )
        processed = []

        if results.get("answer"):
            processed.append({"type": "summary", "content": results["answer"]})

        for r in results.get("results", []):
            processed.append({
                "type": "source",
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:500],
            })

        return processed

    async def search_job_market(self, role: str, preferences: dict = None) -> dict:
        preferences = preferences or {}
        prefer_industry = preferences.get("prefer_industry", [])
        exclude_work_type = preferences.get("exclude_work_type", [])
        industry = f" {' '.join(prefer_industry)}" if prefer_industry else " Thailand"
        exclude = " -startup" if "startup" in exclude_work_type else ""

        queries = [
            f"{role} required skills 2025 2026",
            f"{role} salary{industry}{exclude}",
            f"best courses learn {role} free",
            f"{role} job demand{industry}",
        ]
        results = await asyncio.gather(*[self.search(q) for q in queries])

        return {
            "skills_data": results[0],
            "salary_data": results[1],
            "learning_resources": results[2],
            "market_outlook": results[3],
        }

    async def search_skill_resources(self, skills: list[str]) -> list[dict]:
        all_resources = []

        for skill in skills[:3]:
            results = await self.search(f"best free course learn {skill} 2024", max_results=3)
            all_resources.extend(results)
        return all_resources
