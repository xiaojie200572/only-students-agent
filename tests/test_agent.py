import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRAGService:
    def test_embedder_init(self):
        from app.vector.embedder import Embedder
        
        embedder = Embedder()
        assert embedder.dim == 1024
        assert embedder.model == "bge-m3"

    @pytest.mark.asyncio
    async def test_embed_query(self):
        from app.vector.embedder import Embedder
        
        embedder = Embedder()
        result = await embedder.embed_query("测试文本")
        
        assert isinstance(result, list)
        assert len(result) == 1024

    @pytest.mark.asyncio
    async def test_search_notes(self):
        from app.services.rag import RAGService
        
        with patch("app.services.rag.VectorStore") as mock_vs:
            mock_vs.search = AsyncMock(return_value=[
                {"note_id": 1, "title": "测试笔记", "similarity": 0.9}
            ])
            
            rag_service = RAGService()
            results = await rag_service.search_notes("测试", limit=5)
            
            assert len(results) == 1
            assert results[0]["note_id"] == 1


class TestMemoryService:
    @pytest.mark.asyncio
    async def test_add_message(self):
        from app.services.memory import memory_service
        
        session_id = "test_session_123"
        await memory_service.add_message(session_id, "user", "你好")
        
        history = await memory_service.get_history_async(session_id)
        assert len(history) >= 1


class TestVectorStore:
    def test_collection_name(self):
        from app.vector.client import VectorStore
        
        vs = VectorStore()
        assert vs.collection_name == "notes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
