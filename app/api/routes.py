import uuid
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from app.core.career_service import CareerAdvisorService
from app.core.redis_cache import count_tavily_cache_entries
from app.tools.resume_parser import parse_resume
from app.api.sse import sse_router

router  = APIRouter(prefix="", tags=["career"])
service = CareerAdvisorService() 
router.include_router(sse_router)

# SSE endpoint for workflow progress (node_start/done)
router.include_router(sse_router)

@router.post("/analyze")
async def analyze_career(
    message: str = Form(...),
    thread_id: Optional[str]  = Form(default=None),
    career_goal:  Optional[str]  = Form(default=None),
    preferences:  Optional[str]  = Form(default=None),
    resume_file:  Optional[UploadFile] = File(default=None),
):
    # if not thread_id:
    #     thread_id = str(uuid.uuid4())

    resume_text = None
    if resume_file:
        file_bytes = await resume_file.read()
        
        if len(file_bytes) > 10 * 1024 * 1024:
            raise HTTPException(400, "File too large (max 10MB)")
        try:
            resume_text = await parse_resume(file_bytes, resume_file.filename)
        except ValueError as e:
            raise HTTPException(400, str(e))

    preferences_dict = {}
    if preferences:
        try:
            preferences_dict = json.loads(preferences)
        except Exception:
            pass

    result = await service.analyze(
        thread_id=thread_id,
        message=message,
        resume_text=resume_text,
        career_goal=career_goal,
        preferences=preferences_dict,
    )
    
    if result.get("error"):
        raise HTTPException(500, result["error"])
    return result


@router.post("/chat")
async def chat(
    thread_id: Optional[str] = Form(...),
    message: str = Form(...),
):
    return await service.chat(thread_id=thread_id, message=message)


@router.post("/skill-upgrade")
async def skill_upgrade(
    selected_career:  str = Form(...),
):
    result = await service.request_skill_upgrade(
        selected_career=selected_career,
    )
    if result.get("error"):
        raise HTTPException(500, result["error"])
    return result


@router.get("/health")
async def health():
    cache_entries = await count_tavily_cache_entries()

    return {
        "status":               "ok",
        "storage":              "Redis",
        "tavily_cache_entries": cache_entries,
    }
