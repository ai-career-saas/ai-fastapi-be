from pydantic import BaseModel
from typing import Literal, Optional


class ATSKeywordMatch(BaseModel):
    keyword: str
    found: bool
    importance: Literal["critical", "important", "nice-to-have"] = "important"
    context: Optional[str] = None  # where found in resume


class ATSSection(BaseModel):
    section: str
    score: int = 0       # 0-100
    feedback: str = ""
    issues: list[str] = []


class ATSScoreResult(BaseModel):
    overall_score: int = 0          # 0-100
    grade: str = "C"                # A+, A, B+, B, C+, C, D, F
    keyword_match_rate: int = 0     # percentage
    keyword_matches: list[ATSKeywordMatch] = []
    missing_critical_keywords: list[str] = []
    missing_important_keywords: list[str] = []
    sections: list[ATSSection] = []
    formatting_issues: list[str] = []
    strengths: list[str] = []
    suggestions: list[str] = []
    summary: str = ""               # Thai summary
    estimated_pass_rate: str = ""   # "สูง / ปานกลาง / ต่ำ"
