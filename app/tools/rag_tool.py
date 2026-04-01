from langchain.tools import tool
from app.services import rag_service


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
    results = await rag_service.search_notes(query, limit=limit)

    if not results:
        return "未找到相关笔记"

    formatted = []
    for r in results:
        formatted.append(
            f"- 《{r['title']}》 (相似度: {r['similarity']:.2f})\n"
            f"  摘要: {r.get('summary', r.get('content', '')[:200])}"
        )

    return "\n\n".join(formatted)
