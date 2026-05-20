"""
Exception handlers for the application.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger


class OpsAssistantException(Exception):
    """Base exception for Ops Assistant."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DocumentNotFoundException(OpsAssistantException):
    """Document not found exception."""

    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document not found: {document_id}",
            status_code=404,
        )


class DocumentProcessingException(OpsAssistantException):
    """Document processing exception."""

    def __init__(self, message: str):
        super().__init__(
            message=f"Document processing error: {message}",
            status_code=422,
        )


class RetrievalException(OpsAssistantException):
    """Retrieval exception."""

    def __init__(self, message: str):
        super().__init__(
            message=f"Retrieval error: {message}",
            status_code=500,
        )


class LLMException(OpsAssistantException):
    """LLM generation exception."""

    def __init__(self, message: str):
        super().__init__(
            message=f"LLM error: {message}",
            status_code=500,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for the application."""

    @app.exception_handler(OpsAssistantException)
    async def ops_exception_handler(request: Request, exc: OpsAssistantException):
        logger.error(f"OpsAssistantException: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "status_code": 500,
            },
        )
