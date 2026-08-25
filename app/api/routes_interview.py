from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from app.services.llm_service import call_llm
from app.graph.models.interview_models import InterviewQuestionSet
from app.graph.models.career_graph_models import parse
from app.prompts.ai_prompts import INTERVIEW_GEN_PROMPT
from app.prompts.agentic_prompts import SYSTEM_CAREER_ADVISOR
from app.tools.resume_parser import parse_resume

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/generate")
async def generate_interview_questions(
    target_role: str = Form(...),
    job_description: Optional[str] = Form(default=""),
    experience_level: Optional[str] = Form(default="mid"),
    resume_file: Optional[UploadFile] = File(default=None),
):
    """Generate tailored interview questions for a specific role."""
    resume_text = "No resume provided"
    if resume_file:
        file_bytes = await resume_file.read()
        if len(file_bytes) > 10 * 1024 * 1024:
            raise HTTPException(400, "File too large (max 10MB)")
        try:
            resume_text = await parse_resume(file_bytes, resume_file.filename)
        except ValueError as e:
            raise HTTPException(400, str(e))

    raw = await call_llm(
        system=SYSTEM_CAREER_ADVISOR,
        prompt=INTERVIEW_GEN_PROMPT.format(
            target_role=target_role,
            experience_level=experience_level or "mid",
            job_description=job_description or "Not specified",
            resume_text=resume_text,
        ),
        response_schema=InterviewQuestionSet,
    )

    result: InterviewQuestionSet = parse(InterviewQuestionSet, raw)

    # Ensure IDs are set
    for i, q in enumerate(result.questions):
        q.id = i + 1

    result.total_questions = len(result.questions)
    return result.model_dump()
