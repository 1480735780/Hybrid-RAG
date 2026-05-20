"""
API Router configuration.
"""

from fastapi import APIRouter

from backend.app.api.endpoints import (
    chat,
    documents,
    health,
    knowledge_base,
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"],
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"],
)

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"],
)

api_router.include_router(
    knowledge_base.router,
    prefix="/knowledge-base",
    tags=["knowledge-base"],
)
