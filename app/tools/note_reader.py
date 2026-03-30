from typing import Dict, Any
from langchain.tools import tool
import httpx

from app.config import get_settings

settings = get_settings()


@tool
async def read_note(note_id: int) -> str:
    """
    读取指定笔记的详细内容。当需要获取某篇笔记的完整内容时使用。

    Args:
        note_id: 笔记ID

    Returns:
        笔记的完整内容
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.java_api_base_url}/api/notes/{note_id}",
                timeout=10.0,
            )
            if response.status_code == 200:
                note = response.json()
                return f"""笔记标题: {note.get("title", "无标题")}
作者: {note.get("author_name", "未知")}
内容:
{note.get("content", "无内容")}"""
            else:
                return f"无法获取笔记 {note_id}，状态码: {response.status_code}"
        except Exception as e:
            return f"获取笔记失败: {str(e)}"
