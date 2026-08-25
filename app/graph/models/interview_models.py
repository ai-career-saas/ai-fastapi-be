from pydantic import BaseModel
from typing import Literal, Optional


class InterviewQuestion(BaseModel):
    id: int = 0
    category: Literal["technical", "behavioral", "situational", "culture_fit"]
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    question: str
    why_asked: str          # Thai explanation
    key_points: list[str] = []
    sample_answer_tip: str  # Thai tips
    follow_up: Optional[str] = None


class InterviewQuestionSet(BaseModel):
    target_role: str
    experience_level: str = "mid"
    total_questions: int = 0
    questions: list[InterviewQuestion] = []
    preparation_tips: list[str] = []
    overall_advice: str = ""
