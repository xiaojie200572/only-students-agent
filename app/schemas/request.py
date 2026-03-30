from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    session_id: str
    message: str
    use_rag: bool = True
    use_agent: bool = False


class MentionRequest(BaseModel):
    note_id: int
    comment_id: int
    user_id: int
    content: str


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class SyncRequest(BaseModel):
    full_sync: bool = False
    since_id: Optional[int] = None
