from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

from app.schemas.request import ChatRequest
from app.schemas.response import ChatResponse, Source
from app.services.rag import RAGService
from app.services.memory import MemoryService

router = APIRouter()
rag_service = RAGService()
memory_service = MemoryService()


async def chat_event_generator(request: ChatRequest):
    history = memory_service.get_history(request.session_id)

    yield {"event": "status", "data": json.dumps({"type": "status", "content": "thinking"})}

    async for chunk in rag_service.chat_stream(
        message=request.message,
        history=history,
        use_rag=request.use_rag,
    ):
        if chunk.get("type") == "source":
            sources = [
                Source(
                    note_id=s["note_id"],
                    title=s["title"],
                    similarity=s["similarity"],
                )
                for s in chunk.get("sources", [])
            ]
            yield {"event": "done", "data": json.dumps({"type": "done", "sources": [s.model_dump() for s in sources]})}
        else:
            yield {"event": "content", "data": json.dumps({"type": "content", "content": chunk.get("content", "")})}

    memory_service.add_message(request.session_id, "user", request.message)
    memory_service.add_message(request.session_id, "assistant", chunk.get("content", ""))


@router.post("/chat")
async def chat(request: ChatRequest):
    return EventSourceResponse(chat_event_generator(request))


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    history = memory_service.get_history(session_id)
    return {"session_id": session_id, "messages": history}
