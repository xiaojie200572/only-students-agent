from fastapi import APIRouter
from app.api import chat, search, mention, knowledge

api_router = APIRouter()

api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(search.router,  tags=["search"])
api_router.include_router(mention.router, tags=["mentions"])
api_router.include_router(knowledge.router, tags=["knowledge"])
