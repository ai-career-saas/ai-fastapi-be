# AI Career Advisor — FastAPI Backend

The AI/agentic backend for **AI Career Advisor**, a multi-service career-guidance platform. This service owns the LangGraph-based reasoning pipeline: analyzing a user's resume and goals, mapping skill gaps, researching the job market, and producing a personalized roadmap — plus on-demand ATS resume scoring and interview-question generation.

It is designed to sit behind a NestJS API gateway (see `nestjs_api_url` in config) as part of a larger microservice architecture.

## Features

- **Career analysis workflow** — a LangGraph state machine that branches depending on whether the user has a stated career goal:
  - **Goal-driven path**: skill-gap analysis → market research (Tavily) → roadmap generation → validation
  - **Exploratory path**: skill analysis → sufficiency check → full career recommendations or multi-career gap analysis → validation
  - A validation node can trigger a bounded retry back into the roadmap/recommendation nodes before producing the final response
- **Resume parsing** — accepts PDF, DOCX, or TXT resumes and extracts text server-side
- **ATS resume scoring** (`/ats/score`) — scores a resume against a job description and returns a letter grade
- **Interview question generation** (`/interview/generate`) — produces tailored interview questions for a target role, experience level, and (optionally) an uploaded resume
- **Live workflow progress via SSE** (`/stream`) — streams `node_start` / `done` events as the graph executes
- **Redis-backed caching** — caches Tavily search results (TTL-based) and exposes a cache health metric
- **Checkpointed conversations** — LangGraph `MemorySaver` checkpointing keyed by `thread_id`, enabling multi-turn `/chat` follow-ups

## Tech Stack

| Layer | Technology |
| --- | --- |
| Framework | FastAPI |
| Agent orchestration | LangGraph |
| LLM | Google Gemini |
| Web search | Tavily |
| Cache / checkpoint store | Redis |
| Resume parsing | `pdfplumber`, `python-docx` |
| Validation | Pydantic v2 / `pydantic-settings` |
| Server | Uvicorn |
| Container | Docker |

## Project Structure

```
app/
├── main.py                  # FastAPI app, lifespan (Redis), CORS, router registration
├── api/
│   ├── routes.py            # /analyze, /chat, /skill-upgrade, /health
│   ├── routes_ats.py        # /ats/score
│   ├── routes_interview.py  # /interview/generate
│   └── sse.py                # /stream — Server-Sent Events for workflow progress
├── core/
│   ├── config.py             # Settings (env-driven, pydantic-settings)
│   ├── logging.py
│   ├── redis_cache.py        # Redis init/close, Tavily cache helpers
│   └── career_service.py     # Orchestrates the LangGraph workflows
├── graph/
│   ├── career_graph.py       # StateGraph definition (nodes + edges)
│   ├── routes.py             # Conditional routing / retry logic
│   └── models/                # Pydantic response schemas (ATS, interview, career graph)
├── nodes/                     # Individual LangGraph node implementations
│   ├── analyze_goal.py
│   ├── analyze_skills.py
│   ├── market.py
│   ├── roadmap.py
│   └── validate.py
├── services/
│   ├── llm_service.py         # Gemini call wrapper + structured-output parsing
│   ├── search_service.py
│   └── cache_service.py
├── tools/
│   ├── resume_parser.py       # PDF/DOCX/TXT text extraction
│   └── search_tool.py         # Tavily search wrapper
├── prompts/                    # LLM prompt templates
└── models/
    └── state.py                # CareerState — shared LangGraph state schema
```

## Getting Started

### Prerequisites

- Python 3.13
- Redis instance
- Google Gemini API key
- Tavily API key

### Installation

```bash
git clone https://github.com/ai-career-saas/ai-fastapi-be.git
cd ai-fastapi-be
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
ENVIRONMENT=development
LOG_LEVEL=INFO

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite

TAVILY_API_KEY=your_tavily_api_key

NESTJS_API_URL=http://localhost:3000
REDIS_URL=redis://localhost:6379
```

### Run locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`, with interactive docs at `/docs`.

### Run with Docker

```bash
docker build -t ai-career-fastapi-be .
docker run -p 8000:8000 --env-file .env ai-career-fastapi-be
```

## API Overview

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | App-level health check |
| `POST` | `/analyze` | Run the career analysis graph (message, optional resume, career goal, preferences) |
| `POST` | `/chat` | Continue an existing analysis thread (`thread_id` required) |
| `POST` | `/skill-upgrade` | Generate a skill-upgrade plan for a selected career |
| `GET` | `/health` (career router) | Service health + Tavily cache entry count |
| `GET` | `/stream` | SSE stream of workflow node progress |
| `POST` | `/ats/score` | Score a resume against a job description (ATS simulation) |
| `POST` | `/interview/generate` | Generate tailored interview questions for a target role |

## Notes

- CORS is currently restricted to the configured `NESTJS_API_URL`, reflecting this service's role behind a NestJS gateway rather than being called directly by a browser client.
- Conversation state and retry bookkeeping are held in the `CareerState` TypedDict and checkpointed in-memory per `thread_id`; swap `MemorySaver` for a persistent LangGraph checkpointer before running multiple instances in production.
