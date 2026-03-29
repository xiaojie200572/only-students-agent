from typing import List
import httpx

from app.config import get_settings

settings = get_settings()


class Embedder:
    def __init__(self):
        self.api_url = settings.dashscope_base_url
        self.model = settings.embedding_model
        self.dim = settings.embedding_dim
        self.api_key = settings.dashscope_api_key

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def embed_query(self, text: str) -> List[float]:
        async with httpx.AsyncCalient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/embeddings",
                    headers=self._get_headers(),
                    json={
                        "model": self.model,
                        "input": text,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
                return result["data"][0]["embedding"]
            except Exception as e:
                print(f"Embedding error: {e}")
                return [0.0] * self.dim

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/embeddings",
                    headers=self._get_headers(),
                    json={
                        "model": self.model,
                        "input": texts,
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                result = response.json()
                return [item["embedding"] for item in result["data"]]
            except Exception as e:
                print(f"Batch embedding error: {e}")
                return [[0.0] * self.dim for _ in texts]

    async def embed_documents(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = await self.embed_texts(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings


embedder = Embedder()
