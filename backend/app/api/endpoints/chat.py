"""
Chat endpoints for RAG-based conversation.
"""

from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

router = APIRouter()

# Global RAG service instance
_rag_service = None
_document_service = None


def get_rag_service():
    """Get or create RAG service."""
    global _rag_service
    if _rag_service is None:
        from backend.app.services.rag_service import RAGService
        _rag_service = RAGService()
    return _rag_service


def get_document_service():
    """Get or create document service."""
    global _document_service
    if _document_service is None:
        from backend.app.services.document_service import DocumentService
        _document_service = DocumentService()
    return _document_service


# Request/Response Models
class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    metadata: Optional[dict] = None


class ChatRequest(BaseModel):
    """Chat request model."""
    query: str = Field(..., description="User query", min_length=1, max_length=4000)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    history: List[ChatMessage] = Field(default_factory=list, description="Chat history")
    metadata_filter: Optional[dict] = Field(None, description="Metadata filters for retrieval")
    use_hybrid: bool = Field(True, description="Use hybrid retrieval (BM25 + Vector)")
    top_k: int = Field(5, description="Number of results to return", ge=1, le=20)


class SourceDocument(BaseModel):
    """Source document model."""
    content: str = Field(..., description="Document content")
    metadata: dict = Field(default_factory=dict, description="Document metadata")
    score: float = Field(..., description="Relevance score")


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str = Field(..., description="Generated answer")
    session_id: str = Field(..., description="Session ID")
    sources: List[SourceDocument] = Field(default_factory=list, description="Source documents")
    query: str = Field(..., description="Original query")


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a chat query using RAG pipeline.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid4())

        logger.info(f"Processing chat query for session {session_id}")
        logger.debug(f"Query: {request.query}")

        # Get RAG service
        rag_service = get_rag_service()

        # Initialize if needed
        if not rag_service._initialized:
            await rag_service.initialize()

            # Load existing documents
            doc_service = get_document_service()
            all_chunks = doc_service.get_all_chunks()
            if all_chunks:
                rag_service.add_documents(all_chunks)
                logger.info(f"Loaded {len(all_chunks)} chunks into RAG index")

        # Process query
        result = await rag_service.process_query(
            query=request.query,
            history=[msg.dict() for msg in request.history],
            metadata_filter=request.metadata_filter,
            use_hybrid=request.use_hybrid,
            top_k=request.top_k,
        )

        # Format sources
        sources = []
        for doc in result.get("sources", []):
            sources.append(SourceDocument(
                content=doc.get("content", ""),
                metadata=doc.get("metadata", {}),
                score=doc.get("score", 0),
            ))

        return ChatResponse(
            answer=result.get("answer", ""),
            session_id=session_id,
            sources=sources,
            query=request.query,
        )

    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response using Server-Sent Events (SSE).
    """
    # TODO: Implement streaming response
    from fastapi.responses import StreamingResponse

    async def generate():
        yield "data: Streaming not implemented yet\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/sessions/{session_id}/history")
async def get_chat_history(session_id: str):
    """
    Get chat history for a session.
    """
    return {"session_id": session_id, "messages": []}


@router.delete("/sessions/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Clear chat history for a session.
    """
    return {"status": "cleared", "session_id": session_id}
