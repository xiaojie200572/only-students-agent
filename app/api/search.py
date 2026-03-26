from fastapi import APIRouter
from app.schemas.request import SearchRequest
from app.schemas.response import SearchResponse
from app.services.rag import RAGService

router = APIRouter()
rag_service = RAGService()


@router.get("/search")
async def search_notes(query: str, limit: int = 5):
    results = await rag_service.search_notes(query, limit=limit)
    return SearchResponse(results=results, total=len(results))
