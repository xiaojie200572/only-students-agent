from langchain.tools import tool
from app.services.rag import rag_service


@tool
async def search_authors(query: str, limit: int = 5) -> str:
    """
    搜索发布相关内容的作者。当用户询问"谁教 Python"、"哪个发布者讲编程"、"帮我找到教 xxx 的老师"时使用。

    Args:
        query: 用户想找的领域或主题
        limit: 返回的作者数量，默认为5

    Returns:
        相关领域的作者列表，包含发布笔记数量和代表作品
    """
    results = await rag_service.search_authors(query, limit=limit)

    if not results:
        return "未找到发布相关内容的作者"

    formatted = []
    for i, author in enumerate(results, 1):
        note_titles = "、".join(author["note_titles"]) if author["note_titles"] else "暂无"
        formatted.append(
            f"{i}. {author['author_name']} ({author['note_count']}篇笔记)\n"
            f"   代表笔记: {note_titles}"
        )

    return "\n\n".join(formatted)
