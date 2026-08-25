from app.graph.career_graph import career_graph, upgrade_graph
from app.models.state import CareerState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.prompts.agentic_prompts import SYSTEM_CAREER_ADVISOR
from app.core.config import get_settings

THREAD_ID = "default" 

def config(thread_id: str = THREAD_ID) -> dict:
    return {"configurable": {"thread_id": thread_id}}

def to_dict(value) -> dict:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {}

class CareerAdvisorService:
    async def analyze(
        self,
        thread_id: str,
        message: str,
        resume_text: str | None = None,
        career_goal: str | None = None,
        preferences: dict | None = None,
    ) -> dict:

        initial_state: CareerState = {
            "message":                     message,
            "resume_text":                 resume_text,
            "career_goal":                 career_goal,
            "has_career_goal":             None,
            "current_profile":             None,
            "preferences":                 preferences or {},
            "detected_skills":             None,
            "skill_sufficient":            None,
            "career_skill_coverage":       None,
            "recommended_careers":         None,
            "ready_careers":               None,
            "near_reach_careers":          None,
            "skill_gaps":                  None,
            "selected_career_for_upgrade": None,
            "skill_upgrade_plan":          None,
            "market_data":                 None,
            "roadmap":                     None,
            "path_type":                   None,
            "previous_node":               None,
            "validation_result":           None,
            "validation_passed":           None,
            "validation_retry_count":      0,
            "final_response":              None,
            "error":                       None,
        }

        final_state = await career_graph.ainvoke(
            initial_state,
            config=config(thread_id),
        )

        return self.build_response(final_state)
    
    async def chat(self, message: str, thread_id: str) -> dict:
        settings = get_settings()

        snapshot = career_graph.get_state(config(thread_id))
        history: list = []

        if snapshot and snapshot.values:
            v = snapshot.values
            if v.get("career_goal"):
                history.append(AIMessage(content=f"เคยวิเคราะห์: เป้าหมาย {v['career_goal']}"))
            if (v.get("current_profile") or {}).get("summary"):
                history.append(AIMessage(content=v["current_profile"]["summary"]))
            if v.get("final_response"):
                history.append(AIMessage(content=v["final_response"][:800]))

        chat_llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.7,
        )
        messages = [SystemMessage(content=SYSTEM_CAREER_ADVISOR)]
        messages.extend(history[-4:])
        messages.append(HumanMessage(content=message))

        response = await chat_llm.ainvoke(messages)
        return {"thread_id": thread_id, "message": response.content}
    
    async def request_skill_upgrade(self, selected_career: str) -> dict:
        """User เลือกอาชีพจาก near_reach_careers → upgrade plan"""
        snapshot = career_graph.get_state(config(THREAD_ID))
        existing = snapshot.values if snapshot else {}

        initial_state: CareerState = {
            "message":                     f"ขอดูแผนพัฒนา skill สำหรับ {selected_career}",
            "resume_text":                 existing.get("resume_text"),
            "career_goal":                 selected_career,
            "has_career_goal":             True,
            "current_profile":             existing.get("current_profile"),
            "preferences":                 existing.get("preferences", {}),
            "detected_skills":             existing.get("detected_skills", []),
            "skill_sufficient":            None,
            "career_skill_coverage":       None,
            "recommended_careers":         None,
            "ready_careers":               existing.get("ready_careers", []),
            "near_reach_careers":          None,
            "skill_gaps":                  None,
            "selected_career_for_upgrade": selected_career,
            "skill_upgrade_plan":          None,
            "market_data":                 None,
            "roadmap":                     None,
            "path_type":                   "skill_upgrade",
            "previous_node":               None,
            "validation_result":           None,
            "validation_passed":           None,
            "validation_retry_count":      0,
            "final_response":              None,
            "error":                       None,
        }

        final_state = await upgrade_graph.ainvoke(
            initial_state,
            config=config(f"{THREAD_ID}_upgrade_{selected_career}"),
        )
        return {
            "selected_career":    selected_career,
            "skill_upgrade_plan": final_state.get("skill_upgrade_plan"),
            "message":            final_state.get("final_response", ""),
            "error":              final_state.get("error"),
        }

    def build_response(self, state: CareerState) -> dict:
        path = state.get("path_type", "has_goal")
        ma = to_dict((state.get("market_data") or {}).get("analysis", {}))
        val = to_dict(state.get("validation_result") or {})
        warnings  = [i for i in val.get("issues", []) if i.get("severity") == "warning"]
        critical  = [i for i in val.get("issues", []) if i.get("severity") == "critical"]

        if path == "no_goal_sufficient":
            analysis = {
                "path_type":           path,
                "detected_skills":     state.get("detected_skills") or [],
                "ready_careers":       state.get("ready_careers") or [],
                "near_reach_careers":  state.get("near_reach_careers") or [],
                "recommended_careers": state.get("recommended_careers") or [],
                "skill_sufficient":    True,
            }
        elif path == "no_goal_insufficient":
            analysis = {
                "path_type":            path,
                "detected_skills":      state.get("detected_skills") or [],
                "recommended_careers":  state.get("recommended_careers") or [],
                "easiest_path":         ma.get("easiest_path"),
                "highest_salary_path":  ma.get("highest_salary_path"),
                "overall_advice":       ma.get("overall_advice"),
                "skill_sufficient":     False,
            }
        else:  # has_goal
            analysis = {
                "path_type":           path,
                "current_profile":     state.get("current_profile"),
                "detected_skills":     state.get("detected_skills") or [],
                "recommended_careers": state.get("recommended_careers") or [],
                "skill_gaps":          state.get("skill_gaps") or [],
                "roadmap":             state.get("roadmap"),
                "market_insights":     ma.get("market_insights", []),
                "salary_range":        ma.get("salary_range"),
                "preferences_applied": state.get("preferences", {}),
            }

        return {
            "path_type": path,
            "message":   state.get("final_response", ""),
            "analysis":  analysis,
            "validation": {
                "passed":          state.get("validation_passed", True),
                "quality_score":   val.get("overall_quality_score"),
                "summary":         val.get("validation_summary"),
                "warnings":        warnings,
                "critical_issues": critical,
                "retry_count":     state.get("validation_retry_count", 0),
            },
            "error": state.get("error"),
        }
