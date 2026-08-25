import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.state import CareerState

sse_queues: dict[str, asyncio.Queue] = {}
sse_router = APIRouter()


async def emit_event(state: CareerState, event: str, node_id: str, desc: str = ""):
    uid = "default"
    q = sse_queues.get(uid)
    if q:
        await q.put({"event": event, "node": node_id, "desc": desc})


@sse_router.get("/stream")
async def stream():
    user_id = "default"
    q = asyncio.Queue()
    sse_queues[user_id] = q

    async def generator():
        try:
            while True:
                data = await q.get()
                yield f"data: {json.dumps(data)}\n\n"
                if data.get("event") == "done":
                    break
        finally:
            if sse_queues.get(user_id) is q:
                del sse_queues[user_id]

    return StreamingResponse(generator(), media_type="text/event-stream")
