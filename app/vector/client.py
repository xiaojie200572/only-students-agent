from typing import List, Dict, Any, Optional

from pymilvus import MilvusClient, FieldSchema, CollectionSchema, DataType
from pymilvus.milvus_client.index import IndexParams

from app.config import get_settings

settings = get_settings()


class VectorStore:
    def __init__(self):
        self._client = None
        self.collection_name = settings.milvus_collection

    @property
    def client(self):
        if self._client is None:
            if settings.milvus_mode == "lite":
                self._client = MilvusClient(uri=settings.milvus_uri)
            else:
                self._client = MilvusClient(
                    uri=f"http://{settings.milvus_host}:{settings.milvus_port}"
                )
            self._ensure_collection()
        return self._client

    def _ensure_collection(self) -> None:
        if not self._client.has_collection(self.collection_name):
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
                FieldSchema(name="note_id", dtype=DataType.INT64),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="summary", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="author_id", dtype=DataType.INT64),
                FieldSchema(name="author_name", dtype=DataType.VARCHAR, max_length=128),
                FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(
                    name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.embedding_dim
                ),
            ]

            schema = CollectionSchema(fields=fields, description="Notes collection for RAG")

            self._client.create_collection(
                collection_name=self.collection_name,
                schema=schema,
            )

            index_params = IndexParams()
            index_params.add_index(
                field_name="embedding",
                index_type="AUTOINDEX",
                metric_type="COSINE",
            )

            self._client.create_index(
                collection_name=self.collection_name,
                index_params=index_params,
            )

            self._client.load_collection(self.collection_name)

    """
    CRUD
    """

    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                data=[query_vector],
                limit=top_k,
                output_fields=["note_id", "title", "content", "summary", "author_name", "tags"],
            )

            if not results or not results[0]:
                return []

            formatted = []
            for hit in results[0]:
                formatted.append(
                    {
                        "note_id": hit["entity"]["note_id"],
                        "title": hit["entity"]["title"],
                        "content": hit["entity"].get("content", ""),
                        "summary": hit["entity"].get("summary", ""),
                        "author_name": hit["entity"].get("author_name", ""),
                        "tags": hit["entity"].get("tags", ""),
                        "similarity": float(1 / (1 + hit["distance"]))
                        if hit["distance"] > 0
                        else 1.0,
                    }
                )

            return formatted
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def insert(self, notes: List[Dict[str, Any]]) -> int:
        if not notes:
            return 0

        data = []
        for note in notes:
            data.append(
                {
                    "id": note.get("id", note["note_id"]),
                    "note_id": note["note_id"],
                    "title": note.get("title", ""),
                    "content": note.get("content", ""),
                    "summary": note.get("summary", note.get("content", "")[:500]),
                    "author_id": note.get("author_id", 0),
                    "author_name": note.get("author_name", ""),
                    "tags": ",".join(note.get("tags", [])),
                    "embedding": note["embedding"],
                }
            )

        self.client.insert(collection_name=self.collection_name, data=data)
        self.client.flush(collection_name=self.collection_name)

        return len(data)

    def delete_by_ids(self, ids: List[int]) -> None:
        self.client.delete(
            collection_name=self.collection_name,
            pks=ids,
        )

    def get_count(self) -> int:
        try:
            return self.client.query(
                collection_name=self.collection_name,
                output_fields=["count(*)"],
            )[0]["count(*)"]
        except Exception:
            return 0

    def clear(self) -> None:
        if self.client.has_collection(self.collection_name):
            self.client.drop_collection(self.collection_name)
            self._ensure_collection()


vector_store = VectorStore()
