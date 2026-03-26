from pydantic import BaseModel
from typing import Optional, List, Any


class Source(BaseModel):
    note_id: int
    title: str
    similarity: float


class ChatResponse(BaseModel):
    type: str
    content: Optional[str] = None
    sources: Optional[List[Source]] = None


class SearchResponse(BaseModel):
    results: List[dict]
    total: int


class MentionResponse(BaseModel):
    success: bool
    reply_content: str


class SyncResponse(BaseModel):
    success: bool
    synced_count: int
    message: str


class HistoryResponse(BaseModel):
    session_id: str
    messages: List[dict]
