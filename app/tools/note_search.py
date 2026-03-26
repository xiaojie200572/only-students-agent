from typing import List, Dict, Any
from langchain.tools import tool
import httpx

from app.config import get_settings
from app.vector.client import VectorStore
from app.vector.embedder import Embedder

settings = get_settings()
vector_store = VectorStore()
embedder = Embedder()


@tool
async def search_notes(query: str, limit: int = 5) -> str:
    """
    搜索站内笔记内容。当用户询问关于某个主题的笔记时使用。
    
    Args:
        query: 搜索关键词
        limit: 返回结果数量，默认为5
    
    Returns:
        相关笔记列表，包含标题和摘要
    """
    query_vector = await embedder.embed_query(query)
    
    results = await vector_store.search(
        query_vector=query_vector,
        top_k=limit,
    )
    
    if not results:
        return "未找到相关笔记"
    
    formatted = []
    for r in results:
        formatted.append(
            f"- 《{r['title']}》 (相似度: {r['similarity']:.2f})\n"
            f"  摘要: {r.get('summary', r.get('content', '')[:200])}"
        )
    
    return "\n\n".join(formatted)


@tool
def get_search_notes_schema() -> Dict[str, Any]:
    return {
        "name": "search_notes",
        "description": "搜索站内笔记内容。当用户询问关于某个主题的笔记时使用。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量，默认为5",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    }
