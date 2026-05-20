"""
FastAPI Application Entry Point.
Enterprise Intelligent Ops Assistant Based on Hybrid RAG.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.config.settings import get_settings
from backend.app.api import api_router
from backend.app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)

    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Server: {settings.HOST}:{settings.PORT}")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"Vector Store: {settings.VECTOR_STORE_TYPE}")

    yield

    # Shutdown
    logger.info("Shutting down application...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Enterprise Intelligent Ops Assistant Based on Hybrid RAG",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "service": settings.APP_NAME,
        }

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Enterprise Ops Assistant API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
