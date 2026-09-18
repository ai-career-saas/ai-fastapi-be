import json

from app.api.sse import emit_event
from app.core.logging import get_logger
from app.graph.models.career_graph_models import (
    parse,
    Node2aOutput,
    Node2bOutput,
    RecommendFullOutput,
    MultiGapOutput,
    SkillUpgradeOutput,
)
from app.models.state import CareerState
from app.prompts.agentic_prompts import (
    SYSTEM_CAREER_ADVISOR,
    NODE2_ANALYZE_SKILLS,
    NODE2_ANALYZE_SKILLS_WITH_GOAL,
    NODE_RECOMMEND,
    NODE_MULTI_CAREER_GAP,
    NODE_SKILL_UPGRADE,
)
from app.services.cache_service import search_cached
from app.services.llm_service import call_llm
from app.tools.search_tool import CareerSearchTool

logger = get_logger(__name__)


async def analyze_skills(state: CareerState) -> CareerState:
    logger.info("Node 2: Skills check")
    await emit_event(state, "node_start", "node2_skills", "Analyzing your skills...")

    try:
        tool = CareerSearchTool()
        profile = state.get("current_profile", {})
        prefs_json = json.dumps(state.get("preferences", {}), ensure_ascii=False)

        ind = " ".join(state.get("preferences", {}).get("prefer_industry", []))
        market_results = await search_cached(
            tool, f"in-demand tech careers required skills Thailand {ind}".strip()
        )
        market_data_json = json.dumps(market_results, ensure_ascii=False)

        raw = await call_llm(
            system=SYSTEM_CAREER_ADVISOR,
            prompt=NODE2_ANALYZE_SKILLS.format(
                current_role=profile.get("current_role", "Unknown"),
                years_experience=profile.get("years_experience", "Unknown"),
                education=profile.get("education", "Unknown"),
                resume_text=state.get("resume_text") or "No resume provided",
                message=state.get("message", ""),
                preferences=prefs_json,
                market_data=market_data_json,
            ),
            response_schema=Node2aOutput,
        )
        result: Node2aOutput = parse(Node2aOutput, raw)

        years_exp = profile.get("years_experience", 0)
        try:
            years_exp_num = float(str(years_exp).replace("+", ""))
        except (ValueError, TypeError):
            years_exp_num = 0

        if years_exp_num == 0 or str(years_exp).lower() in ("0", "unknown", "none", ""):
            max_coverage = max(
                (c.coverage_percent for c in result.career_skill_coverage), default=0
            )
            if max_coverage < 80:
                result.skill_sufficient = False

        return {
            **state,
            "detected_skills": [s.model_dump() for s in result.detected_skills],
            "skill_sufficient": result.skill_sufficient,
            "career_skill_coverage": [c.model_dump() for c in result.career_skill_coverage],
        }
    except Exception as e:
        return {**state, "error": str(e), "skill_sufficient": False}


async def analyze_gaps(state: CareerState) -> CareerState:
    logger.info("Node2b: Gap analysis for: %s", state.get("career_goal"))
    await emit_event(state, "node_start", "node2_gaps", "Analyzing skill gaps for your career goal...")
    try:
        profile = state.get("current_profile", {})
        prefs_json = json.dumps(state.get("preferences", {}), ensure_ascii=False)

        raw = await call_llm(
            system=SYSTEM_CAREER_ADVISOR,
            prompt=NODE2_ANALYZE_SKILLS_WITH_GOAL.format(
                current_role=profile.get("current_role", "Unknown"),
                years_experience=profile.get("years_experience", "Unknown"),
                education=profile.get("education", "Unknown"),
                career_goal=state.get("career_goal", ""),
                resume_text=state.get("resume_text") or "No resume provided",
                message=state.get("message", ""),
                market_data=json.dumps((state.get("market_data") or {}).get("raw", {}), ensure_ascii=False),
                preferences=prefs_json,
            ),
            response_schema=Node2bOutput,
        )
        result: Node2bOutput = parse(Node2bOutput, raw)

        return {
            **state,
            "detected_skills": [skill.model_dump() for skill in result.detected_skills],
            "skill_gaps": [gap.model_dump() for gap in result.skill_gaps],
            "recommended_careers": [{"title": state.get("career_goal"), "match_score": 0}],
            "path_type": "has_goal",
        }
    except Exception as e:
        logger.warning("Node2b fallback due to error: %s", e)
        return {
            **state,
            "detected_skills": state.get("detected_skills") or [],
            "skill_gaps": state.get("skill_gaps") or [],
            "recommended_careers": [{"title": state.get("career_goal") or "Target Role", "match_score": 0}],
            "path_type": "has_goal",
            "error": None,
        }


async def node_recommend(state: CareerState) -> CareerState:
    logger.info("Node Recommend Career")
    await emit_event(state, "node_start", "recommend_full", "Analyzing recommended career paths...")
    try:
        detected_skills_json = json.dumps(state.get("detected_skills", []), ensure_ascii=False)
        career_coverage_json = json.dumps(state.get("career_skill_coverage", []), ensure_ascii=False, separators=(",", ":"))
        pref_json = json.dumps(state.get("preferences", {}), ensure_ascii=False)

        raw = await call_llm(
            system=SYSTEM_CAREER_ADVISOR,
            prompt=NODE_RECOMMEND.format(
                detected_skills=detected_skills_json,
                career_skill_coverage=career_coverage_json,
                preferences=pref_json,
            ),
            response_schema=RecommendFullOutput,
        )
        result: RecommendFullOutput = parse(RecommendFullOutput, raw)

        ready = [rc.model_dump() for rc in result.ready_careers]

        return {
            **state,
            "ready_careers": ready,
            "near_reach_careers": [career.model_dump() for career in result.near_reach_careers],
            "recommended_careers": ready,
            "path_type": "no_goal_sufficient",
            "previous_node": "recommend_full",
        }
    except Exception as e:
        return {**state, "error": str(e), "path_type": "no_goal_sufficient"}


async def node_multi_career_gap(state: CareerState) -> CareerState:
    logger.info("Node Multi-Career Gap Analysis")
    await emit_event(state, "node_start", "multi_career_gap", "Analyzing career paths when no clear goal is defined...")
    try:
        tool = CareerSearchTool()

        top_skills = [s["name"] for s in (state.get("detected_skills") or [])[:3]]
        query = (
            f"career paths for {' '.join(top_skills)} Thailand 2025 2026"
            if top_skills
            else "entry level tech careers Thailand"
        )
        results = await search_cached(tool, query, max_results=5)
        market_data = {"results": results}

        detected_skills_json = json.dumps(state.get("detected_skills", []), ensure_ascii=False)
        career_coverage_json = json.dumps(state.get("career_skill_coverage", []), ensure_ascii=False)
        market_data_json = json.dumps(market_data, ensure_ascii=False)
        pref_json = json.dumps(state.get("preferences", {}), ensure_ascii=False)

        raw = await call_llm(
            system=SYSTEM_CAREER_ADVISOR,
            prompt=NODE_MULTI_CAREER_GAP.format(
                detected_skills=detected_skills_json,
                career_skill_coverage=career_coverage_json,
                market_data=market_data_json,
                preferences=pref_json,
            ),
            response_schema=MultiGapOutput,
        )
        result: MultiGapOutput = parse(MultiGapOutput, raw)

        return {
            **state,
            "recommended_careers": [career.model_dump() for career in result.recommended_careers],
            "skill_gaps": [],
            "market_data": {"raw": market_data, "analysis": result.model_dump()},
            "path_type": "no_goal_insufficient",
            "previous_node": "multi_gap",
        }
    except Exception as e:
        return {**state, "error": str(e), "path_type": "no_goal_insufficient"}


async def node_skill_upgrade(state: CareerState) -> CareerState:
    logger.info("Node Skill Upgrade for: %s", state.get("selected_career_for_upgrade"))
    career = state.get("selected_career_for_upgrade", "")

    try:
        tool = CareerSearchTool()
        results = await search_cached(tool, f"learn {career} skills courses resources 2024")
        raw = await call_llm(
            system=SYSTEM_CAREER_ADVISOR,
            prompt=NODE_SKILL_UPGRADE.format(
                detected_skills=json.dumps(state.get("detected_skills", []), ensure_ascii=False),
                ready_careers=json.dumps(state.get("ready_careers", []), ensure_ascii=False),
                selected_career=career,
                market_data=json.dumps({"results": results}, ensure_ascii=False)[:2000],
            ),
            response_schema=SkillUpgradeOutput,
        )

        return {**state, "skill_upgrade_plan": raw}
    except Exception as e:
        return {**state, "error": str(e)}
