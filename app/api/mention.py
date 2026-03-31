from fastapi import APIRouter
from app.schemas.request import MentionRequest
from app.schemas.response import MentionResponse
from app.services.rag import rag_service

router = APIRouter()


@router.post("/mentions/{note_id}")
async def handle_mention(note_id: int, request: MentionRequest):
    reply = await rag_service.handle_mention(
        note_id=note_id,
        content=request.content,
        user_id=request.user_id,
    )
    return MentionResponse(success=True, reply_content=reply)
