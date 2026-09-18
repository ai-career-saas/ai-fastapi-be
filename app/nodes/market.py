import asyncio
import json

from app.api.sse import emit_event
from app.core.logging import get_logger
from app.graph.models.career_graph_models import parse, Node3Output
from app.models.state import CareerState
from app.prompts.agentic_prompts import SYSTEM_CAREER_ADVISOR, NODE3_MARKET_ANALYSIS
from app.services.cache_service import search_cached
from app.services.llm_service import call_llm
from app.tools.search_tool import CareerSearchTool

logger = get_logger(__name__)

async def market_agent(state: CareerState) -> CareerState:
    logger.info("Node Market Agent")
    await emit_event(state, "node_start", "node3_market", "Analyzing the job market and career demands...")
    market_data = {}
    
    try:
        tool = CareerSearchTool()
        target_role = state.get("career_goal", "Software Developer")
        preferences = state.get("preferences", {})
        industry = " ".join(preferences.get("prefer_industry", []))
        excludedWorkType = " -startup" if "startup" in preferences.get("exclude_work_type", []) else ""

        results = await asyncio.gather(
            search_cached(tool, f"{target_role} required skills 2025 2026"),
            search_cached(tool, f"{target_role} salary Thailand {industry}{excludedWorkType}"),
            search_cached(tool, f"best courses learn {target_role} free"),
            search_cached(tool, f"{target_role} job demand Thailand"),
        )

        market_data = {
            "skills_data": results[0],
            "salary_data": results[1],
            "learning_resources": results[2],
            "market_outlook": results[3],
        }

        gap_skills = [gap["skill"] for gap in (state.get("skill_gaps") or [])[:3]]
        for skill in gap_skills:
            query = f"best free course learn {skill} 2026"
            skill_results = await search_cached(tool, query, max_results=3)
            market_data.setdefault("skill_resources", []).extend(skill_results)

        skills_json = json.dumps((state.get("detected_skills") or [])[:10])
        skill_gaps_json = json.dumps((state.get("skill_gaps") or [])[:5])
        prefs_json = json.dumps(preferences, ensure_ascii=False)
        ex_work_type_json = json.dumps(preferences.get("exclude_work_type", []), ensure_ascii=False)
        prefer_industry_json = json.dumps(preferences.get("prefer_industry", []), ensure_ascii=False)
        market_json = json.dumps(market_data, ensure_ascii=False)[:3000]

        raw = await call_llm(
            system=SYSTEM_CAREER_ADVISOR,
            prompt=NODE3_MARKET_ANALYSIS.format(
                target_role=target_role,
                current_skills=skills_json,
                skill_gaps=skill_gaps_json,
                preferences=prefs_json,
                exclude_work_type=ex_work_type_json,
                prefer_industry=prefer_industry_json,
                market_data=market_json,
            ),
            response_schema=Node3Output,
        )
        result: Node3Output = parse(Node3Output, raw)

        return {
            **state,
            "market_data": {"raw": market_data, "analysis": result.model_dump()},
            "skill_gaps": [gap.model_dump() for gap in result.updated_skill_gaps],
        }
    except Exception as e:
        logger.warning("Node3 fallback due to error: %s", e)
        fallback_analysis = {
            "updated_skill_gaps": state.get("skill_gaps") or [],
            "salary_range": {},
            "market_insights": [],
            "top_companies": [],
            "market_trend": "",
        }
        return {
            **state,
            "market_data": {"raw": market_data, "analysis": fallback_analysis},
            "error": None,
        }
