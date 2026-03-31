from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx

from app.config import get_settings
from app.services.llm import llm_service
from app.vector.client import VectorStore
from app.vector.embedder import Embedder

settings = get_settings()


class RAGService:
    def __init__(self):
        self.vector_store = VectorStore()
        self.embedder = Embedder()

    """
    向量库中搜索近似笔记
    """

    async def search_notes(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_vector = await self.embedder.embed_query(query)

        results = await self.vector_store.search(
            query_vector=query_vector,
            top_k=limit,
        )

        return results

    """
    处理评论恢复
    """
    async def handle_mention(self, note_id: int, content: str, user_id: int) -> str:
        note = await self._get_note_detail(note_id)

        if not note:
            return "抱歉，无法获取该笔记的详细信息。"

        prompt = f"""用户 {user_id} 在笔记《{note["title"]}》下评论了 "{content}"。

                请根据该笔记的内容，友好地回复用户的问题或评论。
                笔记内容：{note.get("content", note.get("summary", ""))}

                回复："""

        response = llm_service.chat(message=prompt, context="")
        return response



    """
    获取上下文
    """
    async def _retrieve_context(self, query: str, top_k: int = 5) -> tuple[str, List[Dict]]:
        query_vector = await self.embedder.embed_query(query)

        results = await self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
        )

        if not results:
            return "", []

        context_parts = []
        for r in results:
            context_parts.append(f"笔记《{r['title']}》:\n{r.get('content', r.get('summary', ''))}")

        context = "\n\n---\n\n".join(context_parts)
        return context, results

    """
    从后端获取笔记详情
    """
    async def _get_note_detail(self, note_id: int) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.java_api_base_url}/api/notes/{note_id}",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return response.json()
            except Exception:
                pass
        return None


rag_service = RAGService()
