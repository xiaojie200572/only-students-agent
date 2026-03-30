from asyncio.log import logger

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

from app.schemas.request import ChatRequest
from app.schemas.response import ChatResponse, Source
from app.services.rag import RAGService
from app.services.agent import AgentService
from app.services.memory import MemoryService

router = APIRouter()
rag_service = RAGService()
agent_service = AgentService()
memory_service = MemoryService()


async def chat_event_generator(request: ChatRequest):
    await memory_service.add_message(request.session_id, "user", request.message)

    history = await memory_service.get_history_async(request.session_id)

    yield {"event": "status", "data": json.dumps({"type": "status", "content": "thinking"})}

    full_content = []
    sources = None
    tools_used = []

    try:
        if request.use_agent:
            async for chunk in agent_service.chat_stream(
                message=request.message,
                history=history,
            ):
                if not isinstance(chunk, dict):
                    logger.warning(f"Unexpected chunk: {chunk}")
                    continue

                chunk_type = chunk.get("type")

                if chunk_type == "tool_start":
                    tool_name = chunk.get("tool", "")
                    tools_used.append(tool_name)
                    yield {
                        "event": "tool",
                        "data": json.dumps({"type": "tool_start", "tool": tool_name}),
                    }
                elif chunk_type == "tool_end":
                    tool_name = chunk.get("tool", "")
                    yield {
                        "event": "tool",
                        "data": json.dumps({"type": "tool_end", "tool": tool_name}),
                    }
                elif chunk_type == "content":
                    content = chunk.get("content", "")
                    if content:
                        full_content.append(content)
                        yield {
                            "event": "content",
                            "data": json.dumps({"type": "content", "content": content}),
                        }
                elif chunk_type == "error":
                    yield {
                        "event": "error",
                        "data": json.dumps({"type": "error", "content": chunk.get("content", "")}),
                    }
        else:
            async for chunk in rag_service.chat_stream(
                message=request.message,
                history=history,
                use_rag=request.use_rag,
            ):
                if not isinstance(chunk, dict):
                    logger.warning(f"Unexpected chunk: {chunk}")
                    continue

                chunk_type = chunk.get("type")

                if chunk_type == "source":
                    sources = [
                        Source(
                            note_id=s["note_id"],
                            title=s["title"],
                            similarity=s["similarity"],
                        )
                        for s in chunk.get("sources", [])
                    ]
                    yield {
                        "event": "source",
                        "data": json.dumps(
                            {"type": "source", "sources": [s.model_dump() for s in sources]}
                        ),
                    }

                elif chunk_type == "content":
                    content = chunk.get("content", "")
                    full_content.append(content)
                    yield {
                        "event": "content",
                        "data": json.dumps({"type": "content", "content": content}),
                    }
                else:
                    content = chunk.get("content", "")
                    if content:
                        full_content.append(content)
                        yield {
                            "event": "content",
                            "data": json.dumps({"type": "content", "content": content}),
                        }

        complete_response = "".join(full_content)
        await memory_service.add_message(request.session_id, "assistant", complete_response)

        yield {
            "event": "done",
            "data": json.dumps(
                {
                    "type": "done",
                    "content": complete_response,
                    "sources": [s.model_dump() for s in sources] if sources else [],
                    "tools": tools_used if tools_used else [],
                }
            ),
        }

    except Exception as e:
        logger.error(f"Chat stream error: {e}")
        yield {"event": "error", "data": json.dumps({"type": "error", "message": str(e)})}
        raise


@router.post("/chat")
async def chat(request: ChatRequest):
    return EventSourceResponse(chat_event_generator(request))


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    history = await memory_service.get_history_async(session_id)
    return {"session_id": session_id, "messages": history}
