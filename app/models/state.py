from typing import TypedDict, Optional


class CareerState(TypedDict):
    message: str
    resume_text: Optional[str]
    career_goal: Optional[str]
    has_career_goal: Optional[bool]
    current_profile: Optional[dict]
    preferences: Optional[dict]

    # Skill analysis
    detected_skills: Optional[list]
    skill_sufficient: Optional[bool]
    career_skill_coverage: Optional[list]

    # Output per path
    recommended_careers: Optional[list]
    ready_careers: Optional[list]
    near_reach_careers: Optional[list]
    skill_gaps: Optional[list]

    # Skill upgrade (on-demand)
    selected_career_for_upgrade: Optional[str]
    skill_upgrade_plan: Optional[dict]

    # Market + Roadmap (has_goal)
    market_data: Optional[dict]
    roadmap: Optional[dict]

    # Path tracking
    path_type: Optional[str]
    previous_node: Optional[str]

    # Validation
    validation_result: Optional[dict]
    validation_passed: Optional[bool]
    validation_retry_count: Optional[int]

    final_response: Optional[str]
    error: Optional[str]
