from fastapi import APIRouter
from app.api import chat, search, mention, knowledge

api_router = APIRouter()

api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(mention.router, prefix="/mentions", tags=["mentions"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
