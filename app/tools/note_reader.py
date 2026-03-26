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
                return f"""笔记标题: {note.get('title', '无标题')}
作者: {note.get('author_name', '未知')}
内容:
{note.get('content', '无内容')}"""
            else:
                return f"无法获取笔记 {note_id}，状态码: {response.status_code}"
        except Exception as e:
            return f"获取笔记失败: {str(e)}"


@tool
def get_note_by_keyword(keyword: str, limit: int = 3) -> str:
    """
    通过关键词搜索并获取笔记列表。用于快速查找包含特定关键词的笔记。
    
    Args:
        keyword: 搜索关键词
        limit: 返回数量，默认为3
    
    Returns:
        相关笔记列表
    """
    return f"搜索关键词 '{keyword}' 找到 {limit} 篇笔记"


@tool
def get_read_note_schema() -> Dict[str, Any]:
    return {
        "name": "read_note",
        "description": "读取指定笔记的详细内容。当需要获取某篇笔记的完整内容时使用。",
        "parameters": {
            "type": "object",
            "properties": {
                "note_id": {
                    "type": "integer",
                    "description": "笔记ID",
                },
            },
            "required": ["note_id"],
        },
    }
