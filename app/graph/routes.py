from app.models.state import CareerState

MAX_RETRY = 1

RETRY_TARGET: dict[str, str] = {
    "node4": "node4_roadmap",
    "recommend_full": "recommend_full",
    "multi_gap": "multi_career_gap",
}


def route_by_goal(state: CareerState) -> str:
    return "node2_gaps" if state.get("has_career_goal") else "node2_skills"


def route_by_sufficiency(state: CareerState) -> str:
    return "recommend_full" if state.get("skill_sufficient") else "multi_career_gap"


def route_after_validation(state: CareerState) -> str:
    if state.get("validation_passed"):
        return "final_response"

    retry = state.get("validation_retry_count", 0)
    if retry < MAX_RETRY:
        prev = state.get("previous_node", "node4")
        return RETRY_TARGET.get(prev, "final_response")

    return "final_response"
