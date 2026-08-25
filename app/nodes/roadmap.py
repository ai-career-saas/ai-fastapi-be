import datetime
import json

from app.api.sse import emit_event
from app.core.logging import get_logger
from app.graph.models.career_graph_models import parse, Node4Output
from app.models.state import CareerState
from app.prompts.agentic_prompts import SYSTEM_CAREER_ADVISOR, NODE4_CREATE_ROADMAP, FINAL_RESPONSE_TEMPLATE
from app.services.llm_service import call_llm, to_dict

logger = get_logger(__name__)


async def create_roadmap(state: CareerState) -> CareerState:
    logger.info("Node Roadmap Planner")
    await emit_event(state, "node_start", "node4_roadmap", "กำลังสร้าง Learning Roadmap (แผนพัฒนารายขั้น)...")
    retry = state.get("validation_retry_count", 0)

    try:
        market_analysis = to_dict((state.get("market_data") or {}).get("analysis", {}))
        market_raw = (state.get("market_data") or {}).get("raw", {})

        retry_context = ""
        if retry > 0:
            issues = (state.get("validation_result") or {}).get("issues", [])
            if issues:
                retry_context = "\n\nIMPORTANT — Fix these issues:\n" + "\n".join(
                    f"- [{issue['severity']}] {issue['section']}: {issue['issue']} → {issue['fix']}"
                    for issue in issues
                )

        skills_json = json.dumps((state.get("detected_skills") or [])[:10])
        skill_gaps_json = json.dumps((state.get("skill_gaps") or [])[:5])
        market_json = json.dumps(market_analysis.get("market_insights", []), ensure_ascii=False)
        resource_json = json.dumps(market_raw.get("learning_resources", [])[:5], ensure_ascii=False)[:2000]
        prefs_json = json.dumps(state.get("preferences", {}), ensure_ascii=False)

        raw = await call_llm(
            system=SYSTEM_CAREER_ADVISOR,
            prompt=NODE4_CREATE_ROADMAP.format(
                target_role=state.get("career_goal", "Target Role"),
                current_skills=skills_json,
                skill_gaps=skill_gaps_json,
                market_insights=market_json,
                resources_data=resource_json,
                preferences=prefs_json,
            ) + retry_context,
            response_schema=Node4Output,
        )
        result: Node4Output = parse(Node4Output, raw)

        return {**state, "roadmap": result.model_dump(), "previous_node": "node4"}
    except Exception as e:
        logger.warning("Node4 fallback due to error: %s", e)
        fallback_roadmap = {
            "target_role": state.get("career_goal") or "Target Role",
            "total_duration": "8-12 weeks",
            "milestones": [
                {
                    "week": "1-2",
                    "title": "Set learning baseline",
                    "tasks": ["Review core skills", "Create weekly schedule"],
                    "resources": [],
                    "success_metric": "Complete first learning checklist",
                }
            ],
            "key_certifications": [],
            "daily_commitment": "1-2 hours/day",
            "motivational_message": "Keep improving step by step.",
        }
        return {
            **state,
            "roadmap": fallback_roadmap,
            "previous_node": "node4",
            "error": None,
        }


async def final_response(state: CareerState) -> CareerState:
    logger.info("Node Final: Generate final response for user")
    path = state.get("path_type", "has_goal")

    try:
        await emit_event(state, "node_start", "final_response", "กำลังเรียบเรียงคำตอบสุดท้าย...")
        market_analysis = to_dict((state.get("market_data") or {}).get("analysis", {}))

        if path == "no_goal_sufficient":
            summary = {
                "ready_careers_count": len(state.get("ready_careers") or []),
                "near_reach_careers_count": len(state.get("near_reach_careers") or []),
                "skills_count": len(state.get("detected_skills") or []),
            }
        elif path == "no_goal_insufficient":
            summary = {
                "careers_count": len(state.get("recommended_careers") or []),
                "skills_count": len(state.get("detected_skills") or []),
                "easiest_path": market_analysis.get("easiest_path"),
            }
        else:
            summary = {
                "target_role": state.get("career_goal"),
                "skills_count": len(state.get("detected_skills") or []),
                "gap_count": len(state.get("skill_gaps") or []),
                "roadmap_duration": (state.get("roadmap") or {}).get("total_duration"),
                "salary_range": market_analysis.get("salary_range"),
            }

        response = await call_llm(
            system=SYSTEM_CAREER_ADVISOR,
            prompt=FINAL_RESPONSE_TEMPLATE.format(
                message=state["message"],
                path_type=path,
                analysis_summary=json.dumps(summary, ensure_ascii=False),
            ),
            json_mode=False,
        )

        updated = {**state, "final_response": response, "timestamp": datetime.datetime.now()}
        await emit_event(updated, "done", "final_response", "เสร็จสิ้น")
        return updated

    except Exception as e:
        logger.warning("Final Response fallback due to error: %s", e)
        updated = {
            **state,
            "final_response": "การวิเคราะห์เสร็จสิ้นแล้ว กรุณาดูผลลัพธ์ด้านล่าง",
            "timestamp": datetime.datetime.now(),
        }
        await emit_event(updated, "done", "final_response", "เสร็จสิ้น")
        return updated
