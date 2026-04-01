from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx

from app.config import get_settings
from app.services.llm import llm_service
from app.vector import vector_store, embedder

settings = get_settings()


class RAGService:
    def __init__(self):
        self.vector_store = vector_store
        self.embedder = embedder

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

    async def search_authors(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索发布相关内容的作者"""
        notes = await self.search_notes(query, limit=20)

        if not notes:
            return []

        author_stats = {}
        for note in notes:
            author_name = note.get("author_name", "")
            if not author_name:
                continue

            if author_name not in author_stats:
                author_stats[author_name] = {
                    "author_name": author_name,
                    "note_count": 0,
                    "note_titles": [],
                    "note_ids": [],
                }

            author_stats[author_name]["note_count"] += 1
            if len(author_stats[author_name]["note_titles"]) < 3:
                author_stats[author_name]["note_titles"].append(note.get("title", ""))
            author_stats[author_name]["note_ids"].append(note.get("note_id", 0))

        sorted_authors = sorted(author_stats.values(), key=lambda x: x["note_count"], reverse=True)

        return sorted_authors[:limit]

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
