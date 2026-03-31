from typing import Dict, Any
from langchain.tools import tool
import httpx

from app.config import get_settings

settings = get_settings()

EDUCATION_LEVELS = {
    1: "小学",
    2: "初中",
    3: "高中",
    4: "大学",
    5: "硕士",
    6: "博士",
}


@tool
async def get_user_info(user_id: int) -> str:
    """
    获取用户详细信息。当需要了解某个用户的个人信息时使用，例如查看用户的昵称、头像、学校等。

    Args:
        user_id: 用户ID

    Returns:
        用户详细信息，包含昵称、头像、学校、简介等
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.java_api_base_url}/api/users/{user_id}",
                timeout=10.0,
            )
            if response.status_code == 200:
                user = response.json()
                return _format_user_info(user)
            else:
                return f"无法获取用户信息，状态码: {response.status_code}"
        except Exception as e:
            return f"获取用户信息失败: {str(e)}"


@tool
async def get_current_user_info() -> str:
    """
    获取当前登录用户的信息。当需要获取当前用户（发起请求的用户）的详细信息时使用。

    Returns:
        当前用户的详细信息
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.java_api_base_url}/api/users/me",
                headers={"X-API-Key": settings.java_api_key} if settings.java_api_key else {},
                timeout=10.0,
            )
            if response.status_code == 200:
                user = response.json()
                return _format_user_info(user)
            else:
                return f"无法获取当前用户信息，状态码: {response.status_code}"
        except Exception as e:
            return f"获取当前用户信息失败: {str(e)}"


def _format_user_info(user: dict) -> str:
    """格式化用户信息为可读字符串"""
    nickname = user.get("nickname", "未设置昵称")
    avatar = user.get("avatar", "无头像")
    bio = user.get("bio", "暂无简介")
    education_level = user.get("education_level")
    education = EDUCATION_LEVELS.get(education_level, "未知") if education_level else "未设置"
    school_name = user.get("school_name", "未设置")

    info = f"""用户信息：
昵称: {nickname}
头像: {avatar}
学段: {education}
学校: {school_name}
简介: {bio}"""
    return info

