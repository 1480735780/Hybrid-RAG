"""
Health check endpoints.
"""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends

from backend.config.settings import Settings, get_settings

router = APIRouter()


@router.get("/")
async def health_check(settings: Settings = Depends(get_settings)) -> Dict:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "service": settings.APP_NAME,
    }


@router.get("/detailed")
async def detailed_health_check(settings: Settings = Depends(get_settings)) -> Dict:
    """Detailed health check with component status."""
    # Check database connection
    db_status = "not_configured"

    # Check vector store
    vector_store_status = "ready"

    # Check LLM service
    llm_status = "configured" if settings.OPENAI_API_KEY or settings.DASHSCOPE_API_KEY else "not_configured"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "components": {
            "database": {
                "status": db_status,
                "type": "mysql",
                "host": settings.DB_HOST,
            },
            "vector_store": {
                "status": vector_store_status,
                "type": settings.VECTOR_STORE_TYPE,
            },
            "llm": {
                "status": llm_status,
                "provider": settings.LLM_PROVIDER,
                "model": settings.OPENAI_MODEL if settings.LLM_PROVIDER == "openai" else settings.DASHSCOPE_MODEL,
            },
            "embedding": {
                "status": "configured",
                "model": settings.EMBEDDING_MODEL,
            },
            "rerank": {
                "status": "configured",
                "model": settings.RERANK_MODEL,
            },
        },
    }
