from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.checkpointer import init_checkpointer, close_checkpointer
from app.api.routes import router as career_router
from app.api.routes_interview import router as interview_router
from app.api.routes_ats import router as ats_router

settings = get_settings()
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_checkpointer()
    yield
    await close_checkpointer()

app = FastAPI(title="AI Career Advisor API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4000",
        "http://127.0.0.1:3000",
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(career_router)
app.include_router(interview_router)
app.include_router(ats_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}