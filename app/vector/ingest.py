import asyncio
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime

from app.config import get_settings
from app.vector import vector_store, embedder

settings = get_settings()


class NoteIngestor:
    def __init__(self):
        self.vector_store = vector_store
        self.last_sync_time: Optional[datetime] = None
        self.sync_count: int = 0

    async def fetch_notes_from_api(
        self, page: int = 1, page_size: int = 100, since_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            try:
                params = {"page": page, "size": page_size}
                if since_id:
                    params["since_id"] = since_id

                response = await client.get(
                    f"{settings.java_api_base_url}/api/note/published",
                    params=params,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", data.get("list", []))
                return []
            except Exception as e:
                print(f"Fetch notes error: {e}")
                return []

    def prepare_note_text(self, note: Dict[str, Any]) -> str:
        parts = [
            note.get("title", ""),
            note.get("summary", ""),
            note.get("content", ""),
        ]
        tags = note.get("tags", [])
        if tags:
            if isinstance(tags, str):
                tags = tags.split(",")
            parts.append("标签: " + ", ".join(tags))

        return "\n".join(filter(None, parts))

    async def sync_notes(self, full_sync: bool = False, since_id: Optional[int] = None) -> int:
        total_synced = 0
        page = 1
        page_size = 100

        if full_sync:
            self.vector_store.clear()

        while True:
            notes = await self.fetch_notes_from_api(
                page=page, page_size=page_size, since_id=since_id
            )

            if not notes:
                break

            texts = [self.prepare_note_text(note) for note in notes]
            embeddings = await embedder.embed_documents(texts)

            for i, note in enumerate(notes):
                note["embedding"] = embeddings[i]

            count = self.vector_store.insert(notes)
            total_synced += count

            print(f"Synced page {page}: {count} notes")

            if len(notes) < page_size:
                break

            page += 1
            await asyncio.sleep(0.5)

        self.last_sync_time = datetime.now()
        self.sync_count = total_synced

        return total_synced

    def get_sync_status(self) -> Dict[str, Any]:
        return {
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "synced_count": self.sync_count,
            "total_in_vector_db": self.vector_store.get_count(),
        }


async def main():
    ingestor = NoteIngestor()
    count = await ingestor.sync_notes(full_sync=True)
    print(f"Synced {count} notes to vector store")


if __name__ == "__main__":
    asyncio.run(main())
