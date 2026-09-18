from app.api.sse import emit_event
from app.core.logging import get_logger
from app.graph.models.career_graph_models import parse, Node1Output
from app.models.state import CareerState
from app.prompts.agentic_prompts import SYSTEM_CAREER_ADVISOR, NODE1_ANALYZE_GOAL
from app.services.llm_service import call_llm

logger = get_logger(__name__)

async def analyze_goal(state: CareerState) -> CareerState:
    logger.info("Node1: Analyze goal")
    await emit_event(
        state,
        "node_start",
        "node1_analyze",
        "Analyzing career goal and current profile...",
    )

    try:
        raw = await call_llm(
            system=SYSTEM_CAREER_ADVISOR,
            prompt=NODE1_ANALYZE_GOAL.format(
                message=state["message"],
                resume_text=state.get("resume_text") or "none",
            ),
            response_schema=Node1Output,
        )
        result: Node1Output = parse(Node1Output, raw)

        return {
            **state,
            "has_career_goal": result.has_career_goal,
            "career_goal": result.career_goal or state.get("career_goal"),
            "current_profile": {
                "current_role": result.current_role,
                "years_experience": result.years_experience,
                "education": result.education,
                "summary": result.summary,
            },
            "preferences": result.preferences.model_dump(),
            "validation_retry_count": 0,
        }
    except Exception as e:
        return {**state, "error": str(e), "has_career_goal": False, "validation_retry_count": 0}
