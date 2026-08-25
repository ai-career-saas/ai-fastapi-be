import json
import re

from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Literal, Optional

class Skill(BaseModel):
    name: str
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    category: Literal["technical", "soft", "domain"] = "technical"

    @field_validator("category", mode="before")
    @classmethod
    def normalise_category(cls, v):
        mapping = {
            "technical":    "technical",
            "soft":         "soft",
            "domain":       "domain",
            "professional": "domain",
            "business":     "domain",
            "interpersonal":"soft",
            "hard":         "technical",
        }
        return mapping.get(str(v).lower(), "technical")

    @field_validator("level", mode="before")
    @classmethod
    def normalise_level(cls, v):
        mapping = {
            "beginner":     "beginner",
            "junior":       "beginner",
            "basic":        "beginner",
            "intermediate": "intermediate",
            "mid":          "intermediate",
            "advanced":     "advanced",
            "senior":       "advanced",
            "expert":       "advanced",
        }
        return mapping.get(str(v).lower(), "beginner")

class SkillGap(BaseModel):
    skill: str
    importance: Literal["critical", "important", "nice-to-have"] = "important"
    reason: str = ""
    learn_time: str = ""
    free_resource: Optional[str] = None

    @field_validator("importance", mode="before")
    @classmethod
    def normalise_importance(cls, v):
        mapping = {
            "critical":    "critical",
            "high":        "critical",
            "important":   "important",
            "medium":      "important",
            "nice-to-have": "nice-to-have",
            "low":         "nice-to-have",
            "optional":    "nice-to-have",
        }
        return mapping.get(str(v).lower(), "important")

class SalaryRange(BaseModel):
    min: str = ""
    max: str = ""
    currency: str = "THB"
    period: str = "month"

class Resource(BaseModel):
    name: str
    url: str = ""
    type: str = "course"
    cost: Literal["free", "paid"] = "free"

    @field_validator("url", mode="before")
    @classmethod
    def url_must_start_https(cls, v):
        if v and isinstance(v, str) and not v.startswith("https"):
            return ""
        return v

# Node 1 output model

class Preferences(BaseModel):
    exclude_work_type:    list[str] = []
    prefer_work_type:     list[str] = []
    exclude_industry:     list[str] = []
    prefer_industry:      list[str] = []
    location:             Optional[str] = None
    exclude_company_size: list[str] = []
    prefer_company_size:  list[str] = []

class Node1Output(BaseModel):
    has_career_goal:  bool = False
    career_goal:      Optional[str] = None
    current_role:     Optional[str] = None
    years_experience: Optional[float] = None
    education:        Optional[str] = None
    summary:          str = ""
    preferences:      Preferences = Field(default_factory=Preferences)

# Node 2a output model

class CareerCoverage(BaseModel):
    career:           str
    coverage_percent: int = 0
    has_skills:       list[str] = []
    missing_skills:   list[str] = []
    market_required_skills: list[str] = []

class Node2aOutput(BaseModel):
    detected_skills:        list[Skill] = []
    skill_sufficient:       bool = False
    skill_coverage_summary: str = ""
    career_skill_coverage:  list[CareerCoverage] = []

    @field_validator("skill_sufficient", mode="before")
    @classmethod
    def coerce_bool(cls, v):
        if isinstance(v, bool): return v
        if isinstance(v, str): return v.strip().lower() in ("true", "1", "yes")
        return bool(v)


# Node 2b output model

class Node2bOutput(BaseModel):
    detected_skills: list[Skill] = []
    skill_gaps:      list[SkillGap] = []
    gap_summary:     str = ""

# Node 3 output model

class MarketSkillGap(BaseModel):
    skill:        str
    importance:   Literal["critical", "important", "nice-to-have"] = "important"
    reason:       str = ""
    demand_score: float = 0.0

    @field_validator("importance", mode="before")
    @classmethod
    def normalise_importance(cls, v):
        mapping = {
            "critical":     "critical",
            "high":         "important",   # ← was "critical", should be "important"
            "important":    "important",
            "medium":       "important",
            "nice-to-have": "nice-to-have",
            "low":          "nice-to-have",
            "optional":     "nice-to-have",
        }
        return mapping.get(str(v).lower(), "important")

class Node3Output(BaseModel):
    updated_skill_gaps: list[MarketSkillGap] = []
    salary_range:       SalaryRange = Field(default_factory=SalaryRange)
    market_insights:    list[str] = []
    top_companies:      list[str] = []
    market_trend:       str = ""

# NodeRecommend output model

class ReadyCareer(BaseModel):
    title:             str
    match_score:       int = 0
    description:       str = ""
    matched_skills:    list[str] = []
    missing_minor:     list[str] = []
    salary_range:      str = ""
    why_good_fit:      str = ""
    typical_companies: list[str] = []
    time_to_ready:     str = "พร้อมเลย"

class NearReachMissingSkill(BaseModel):
    skill:      str
    importance: Literal["critical", "important", "nice-to-have"] = "important"
    learn_time: str = ""

class NearReachCareer(BaseModel):
    title:              str
    current_coverage:   int = 0
    missing_skills:     list[NearReachMissingSkill] = []
    total_upskill_time: str = ""
    salary_range:       str = ""
    why_worth_it:       str = ""

class RecommendFullOutput(BaseModel):
    ready_careers:          list[ReadyCareer] = []
    near_reach_careers:     list[NearReachCareer] = []
    recommendation_summary: str = ""

# Node Multi Career Gap Analysis output model

class MultiGapCareer(BaseModel):
    title:              str
    difficulty:         Literal["easy", "medium", "hard"] = "medium"
    current_coverage:   int = 0
    match_score:        int = 0
    description:        str = ""
    salary_range:       str = ""
    matched_skills:     list[str] = []
    skill_gaps:         list[SkillGap] = []
    total_upskill_time: str = ""
    roadmap_summary:    list[str] = []
    typical_companies:  list[str] = []
    why_recommended:    str = ""

class MultiGapOutput(BaseModel):
    recommended_careers: list[MultiGapCareer] = []
    easiest_path:        str = ""
    highest_salary_path: str = ""
    overall_advice:      str = ""

# Skill upgrade output model

class UpgradeResource(BaseModel):
    name: str
    url: str = ""
    type: str = "website"
    cost: Literal["free", "paid"] = "free"

class GapAnalysisItem(BaseModel):
    skill: str
    current_level: Literal["none", "beginner", "intermediate", "advanced"] = "none"
    required_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    importance: Literal["critical", "important", "nice-to-have"] = "important"
    reason: str = ""
    learn_time: str = ""
    resources: list[UpgradeResource] = []

class LearningPhase(BaseModel):
    phase: str
    focus: str
    skills: list[str] = []
    milestone: str = ""

class SkillUpgradeOutput(BaseModel):
    target_career: str = ""
    current_coverage: int = 0
    gap_analysis: list[GapAnalysisItem] = []
    learning_roadmap: list[LearningPhase] = []
    total_time: str = ""
    salary_increase: str = ""
    motivation: str = ""

# Node 4 output model

class Milestone(BaseModel):
    week: str
    title: str
    tasks: list[str] = []
    resources: list[Resource] = []
    success_metric: str = ""

class Node4Output(BaseModel):
    target_role: str = ""
    total_duration: str = ""
    milestones: list[Milestone] = []
    key_certifications: list[str] = []
    daily_commitment: str = ""
    motivational_message: str = ""

    @field_validator("milestones")
    @classmethod
    def must_have_milestones(cls, v):
        if not v:
            raise ValueError("roadmap must have at least 1 milestone")
        return v

# Node 5 output model

class ValidationIssue(BaseModel):
    section:  str
    severity: Literal["critical", "warning"] = "warning"
    field:    str = ""
    issue:    str
    fix:      str = ""

    @field_validator("severity", mode="before")
    @classmethod
    def normalise_severity(cls, v):
        mapping = {
            "critical": "critical",
            "high":     "critical",
            "warning":  "warning",
            "medium":   "warning",
            "low":      "warning",
            "info":     "warning",
            "minor":    "warning",
        }
        return mapping.get(str(v).lower(), "warning")

class FixesApplied(BaseModel):
    skills:     Optional[list] = None
    careers:    Optional[list] = None
    skill_gaps: Optional[list] = None
    roadmap:    Optional[dict] = None

class Node5Output(BaseModel):
    is_valid:              bool = True
    overall_quality_score: int = 0
    issues:                list[ValidationIssue] = []
    auto_fixable:          bool = False
    fixes_applied:         FixesApplied = Field(default_factory=FixesApplied)
    validation_summary:    str = ""

# ── parse() — 3-stage fallback ────────────────────────────────────────────────

def coerce_list(val) -> list:
    if isinstance(val, list): return val
    if isinstance(val, dict): return [val]
    if isinstance(val, str):
        if val:
            return [val]
        else:
            return []

    return []

def repair(model: type[BaseModel], raw: dict) -> dict:
    # ป้องกัน error กรณีที่ข้อมูลดิบไม่ใช่ Dictionary
    if not isinstance(raw, dict):
        return {}

    repaired = {}
    hints = model.model_fields # ดึงรายการฟิลด์ทั้งหมดที่ Model ต้องการ

    for key, val in raw.items():
        # ถ้า key นี้ไม่มีใน Model ให้ข้าม
        if key not in hints:
            continue

        # ดูว่าฟิลด์นี้ถูกกำหนด Type hint ไว้ว่าอะไร (เช่น list[str], int, str)
        annotation = str(hints[key].annotation)

        # ถ้าฟิลด์นี้ต้องการ List แต่ได้ข้อมูลแบบอื่นมา ให้แปลงเป็น List
        if "list" in annotation.lower() and not isinstance(val, list):
            val = coerce_list(val)
        if val is None: # ถ้าค่าว่างให้ข้าม
            continue

        repaired[key] = val

    return repaired

def parse(model: type[BaseModel], raw: str | dict) -> BaseModel:
    # ข้อมูลเป็น string
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw)
            if match:
                try:
                    raw = json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    return model()
            else:
                return model()

    # ข้อมูลไม่ใช่ dict หลังจากพยายามแปลงแล้ว ให้คืนค่า default model
    if not isinstance(raw, dict):
        return model()

    # ── Stage 1 ───────────────────────────────────────────────────────────────
    # ลองแปลงข้อมูลดิบเป็นโมเดลโดยตรงก่อน
    try:
        return model.model_validate(raw)
    except ValidationError:
        pass

    # ── Stage 2: repair ───────────────────────────────────────────────────────
    # ถ้าแปลงไม่สำเร็จ ซ่อมแซมข้อมูลดิบ (เช่น แปลงค่าที่ควรเป็น list แต่เป็น string มาเป็น list) แล้วค่อยแปลงอีกครั้ง
    try:
        return model.model_validate(repair(model, raw))
    except ValidationError:
        pass

    # ── Stage 3: field-by-field salvage ──────────────────────────────────────
    # ถ้ายังแปลงไม่สำเร็จอีก ให้แปลงทีละฟิลด์ เพื่อเก็บข้อมูลที่ถูกต้องที่สุดเท่าที่จะทำได้
    salvaged_data = {}
    for field_name in model.model_fields:
        if field_name not in raw:
            continue
        try:
            model.model_validate({field_name: raw[field_name]})
            salvaged_data[field_name] = raw[field_name]
        except ValidationError:
            pass

    return model.model_validate(salvaged_data)