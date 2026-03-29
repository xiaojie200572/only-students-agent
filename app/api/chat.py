from asyncio.log import logger

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
    # 1. 先保存用户消息（确保不丢失）
    await memory_service.add_message(request.session_id, "user", request.message)

    history = await memory_service.get_history_async(request.session_id)

    yield {"event": "status", "data": json.dumps({"type": "status", "content": "thinking"})}

    full_content = []  # 收集完整内容
    sources = None

    try:
        async for chunk in rag_service.chat_stream(
            message=request.message,
            history=history,
            use_rag=request.use_rag,
        ):
            # 防御性检查
            if not isinstance(chunk, dict):
                logger.warning(f"Unexpected chunk: {chunk}")
                continue

            chunk_type = chunk.get("type")

            if chunk_type == "source":
                # 保存 sources，但不结束
                sources = [
                    Source(
                        note_id=s["note_id"],
                        title=s["title"],
                        similarity=s["similarity"],
                    )
                    for s in chunk.get("sources", [])
                ]
                yield {
                    "event": "source",  # 建议用 source 而非 done
                    "data": json.dumps({
                        "type": "source",
                        "sources": [s.model_dump() for s in sources]
                    })
                }

            elif chunk_type == "content":
                content = chunk.get("content", "")
                full_content.append(content)
                yield {
                    "event": "content",
                    "data": json.dumps({"type": "content", "content": content})
                }
            else:
                # 处理其他类型或默认行为
                content = chunk.get("content", "")
                if content:
                    full_content.append(content)
                    yield {
                        "event": "content",
                        "data": json.dumps({"type": "content", "content": content})
                    }

        # 2. 流结束后保存完整回复
        complete_response = "".join(full_content)
        await memory_service.add_message(
            request.session_id,
            "assistant",
            complete_response
        )

        # 3. 发送真正的 done 事件
        yield {
            "event": "done",
            "data": json.dumps({
                "type": "done",
                "content": complete_response,
                "sources": [s.model_dump() for s in sources] if sources else []
            })
        }

    except Exception as e:
        logger.error(f"Chat stream error: {e}")
        yield {
            "event": "error",
            "data": json.dumps({"type": "error", "message": str(e)})
        }
        raise


@router.post("/chat")
async def chat(request: ChatRequest):
    return EventSourceResponse(chat_event_generator(request))


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    history =await memory_service.get_history_async(session_id)
    return {"session_id": session_id, "messages": history}
