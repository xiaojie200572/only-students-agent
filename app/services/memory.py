import json
from typing import List, Dict, Optional
import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()


class MemoryService:

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self.redis_client

    def _get_key(self, session_id: str) -> str:
        return f"agent:chat:{session_id}"

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        client = await self._get_client()
        key = self._get_key(session_id)

        message = json.dumps({"role": role, "content": content})
        await client.rpush(key, message)
        await client.expire(key, settings.redis_session_ttl)

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        return []

    async def get_history_async(self, session_id: str) -> List[Dict[str, str]]:
        client = await self._get_client()
        key = self._get_key(session_id)

        messages = await client.lrange(key, 0, -1)
        return [json.loads(msg) for msg in messages]

    async def clear_history(self, session_id: str) -> None:
        client = await self._get_client()
        key = self._get_key(session_id)
        await client.delete(key)

    async def close(self) -> None:
        if self.redis_client:
            await self.redis_client.close()


memory_service = MemoryService()
