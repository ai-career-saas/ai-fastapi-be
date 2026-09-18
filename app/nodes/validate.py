import json

from app.api.sse import emit_event
from app.core.logging import get_logger
from app.graph.models.career_graph_models import parse, Node5Output
from app.models.state import CareerState
from app.prompts.agentic_prompts import NODE5_VALIDATE
from app.services.llm_service import call_llm, to_dict

logger = get_logger(__name__)

async def validate(state: CareerState) -> CareerState:
    logger.info("Node 5: Validation")
    await emit_event(state, "node_start", "node5_validate", "Validating the generated career plan...")

    try:
        market_data = state.get("market_data") or {}
        market_analysis = to_dict(market_data.get("analysis", {}))

        skills_json = json.dumps((state.get("detected_skills") or [])[:15], ensure_ascii=False)
        careers_json = json.dumps(state.get("recommended_careers") or [], ensure_ascii=False)
        gaps_json = json.dumps((state.get("skill_gaps") or [])[:10], ensure_ascii=False)
        roadmap_json = json.dumps(state.get("roadmap") or {}, ensure_ascii=False)[:3000]
        market_json = json.dumps(market_analysis.get("market_insights", []), ensure_ascii=False)
        prefs_json = json.dumps(state.get("preferences", {}), ensure_ascii=False)

        raw = await call_llm(
            system="You are a strict QA reviewer.",
            prompt=NODE5_VALIDATE.format(
                target_role=state.get("career_goal", "Multiple careers"),
                detected_skills=skills_json,
                recommended_careers=careers_json,
                skill_gaps=gaps_json,
                roadmap=roadmap_json,
                market_insights=market_json,
                preferences=prefs_json,
            ),
            response_schema=Node5Output,
        )
        result: Node5Output = parse(Node5Output, raw)

        critical = [issue for issue in result.issues if issue.severity == "critical"]
        has_no_critical = len(critical) == 0
        has_passing_score = result.overall_quality_score >= 60
        is_passed = has_no_critical and has_passing_score

        updated = {**state, "validation_result": result.model_dump()}

        fixes = result.fixes_applied
        if fixes.skills:
            updated["detected_skills"] = fixes.skills
        if fixes.careers:
            updated["recommended_careers"] = fixes.careers
        if fixes.skill_gaps:
            updated["skill_gaps"] = fixes.skill_gaps
        if fixes.roadmap:
            updated["roadmap"] = fixes.roadmap

        updated["validation_passed"] = is_passed

        if not is_passed:
            retry = state.get("validation_retry_count", 0)
            updated["validation_retry_count"] = retry + 1

        return updated
    except Exception as e:
        logger.warning("Validation fallback due to error: %s", e)
        return {**state, "validation_passed": True}
