from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.redis_cache import init_redis, close_redis
from app.api.routes import router as career_router
from app.api.routes_interview import router as interview_router
from app.api.routes_ats import router as ats_router

settings = get_settings()
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield
    await close_redis()

app = FastAPI(title="AI Career Advisor API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.nestjs_api_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(career_router)
app.include_router(interview_router)
app.include_router(ats_router)