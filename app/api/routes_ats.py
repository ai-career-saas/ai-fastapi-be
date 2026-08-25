from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services.llm_service import call_llm
from app.graph.models.ats_models import ATSScoreResult
from app.graph.models.career_graph_models import parse
from app.prompts.ai_prompts import ATS_SCORE_PROMPT
from app.prompts.agentic_prompts import SYSTEM_CAREER_ADVISOR
from app.tools.resume_parser import parse_resume

router = APIRouter(prefix="/ats", tags=["ats"])


@router.post("/score")
async def score_resume(
    job_description: str = Form(...),
    resume_file: UploadFile = File(...),
):
    """Score a resume against a job description using ATS simulation."""
    file_bytes = await resume_file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 10MB)")

    try:
        resume_text = await parse_resume(file_bytes, resume_file.filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if len(resume_text.strip()) < 50:
        raise HTTPException(400, "Resume content too short or could not be parsed")

    raw = await call_llm(
        system=SYSTEM_CAREER_ADVISOR,
        prompt=ATS_SCORE_PROMPT.format(
            resume_text=resume_text[:4000],  # cap tokens
            job_description=job_description[:2000],
        ),
        response_schema=ATSScoreResult,
    )

    result: ATSScoreResult = parse(ATSScoreResult, raw)

    # Derive grade if not set
    if not result.grade or result.grade == "C":
        score = result.overall_score
        if score >= 90:   result.grade = "A+"
        elif score >= 80: result.grade = "A"
        elif score >= 70: result.grade = "B+"
        elif score >= 60: result.grade = "B"
        elif score >= 50: result.grade = "C+"
        elif score >= 40: result.grade = "C"
        elif score >= 30: result.grade = "D"
        else:             result.grade = "F"

    return result.model_dump()
