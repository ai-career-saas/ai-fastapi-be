from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.logging import get_logger
from app.models.state import CareerState
from app.nodes.analyze_goal import analyze_goal
from app.nodes.analyze_skills import (
    analyze_skills,
    analyze_gaps,
    node_recommend,
    node_multi_career_gap,
    node_skill_upgrade,
)
from app.nodes.market import market_agent
from app.nodes.roadmap import create_roadmap, final_response
from app.nodes.validate import validate
from app.graph.routes import (
    route_by_goal,
    route_by_sufficiency,
    route_after_validation,
)

logger = get_logger(__name__)

_memory = MemorySaver()


def build_career_graph():
    g = StateGraph(CareerState)

    g.add_node("node1_analyze", analyze_goal)
    g.add_node("node2_skills", analyze_skills)
    g.add_node("node2_gaps", analyze_gaps)
    g.add_node("recommend_full", node_recommend)
    g.add_node("multi_career_gap", node_multi_career_gap)
    g.add_node("node3_market", market_agent)
    g.add_node("node4_roadmap", create_roadmap)
    g.add_node("node5_validate", validate)
    g.add_node("final_response", final_response)

    g.set_entry_point("node1_analyze")

    g.add_conditional_edges("node1_analyze", route_by_goal, {
        "node2_gaps": "node2_gaps",
        "node2_skills": "node2_skills",
    })

    g.add_edge("node2_gaps", "node3_market")
    g.add_edge("node3_market", "node4_roadmap")
    g.add_edge("node4_roadmap", "node5_validate")

    g.add_conditional_edges("node2_skills", route_by_sufficiency, {
        "recommend_full": "recommend_full",
        "multi_career_gap": "multi_career_gap",
    })
    g.add_edge("recommend_full", "node5_validate")
    g.add_edge("multi_career_gap", "node5_validate")

    g.add_conditional_edges("node5_validate", route_after_validation, {
        "final_response": "final_response",
        "node4_roadmap": "node4_roadmap",
        "recommend_full": "recommend_full",
        "multi_career_gap": "multi_career_gap",
    })
    g.add_edge("final_response", END)

    return g.compile(checkpointer=_memory)


def build_upgrade_graph():
    g = StateGraph(CareerState)
    g.add_node("skill_upgrade", node_skill_upgrade)
    g.add_node("final_response", final_response)
    g.set_entry_point("skill_upgrade")
    g.add_edge("skill_upgrade", "final_response")
    g.add_edge("final_response", END)
    return g.compile(checkpointer=_memory)


career_graph = build_career_graph()
upgrade_graph = build_upgrade_graph()

logger.info("Career graph module loaded")

# Re-exports for backward compatibility
from app.services.llm_service import call_llm, to_dict  # noqa: E402, F401
from app.api.sse import sse_router, emit_event  # noqa: E402, F401
