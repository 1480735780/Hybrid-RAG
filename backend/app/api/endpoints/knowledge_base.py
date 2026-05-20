"""
Knowledge base management endpoints.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

router = APIRouter()

# Global services
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
class KnowledgeBaseStats(BaseModel):
    """Knowledge base statistics."""
    total_documents: int = Field(0, description="Total number of documents")
    total_chunks: int = Field(0, description="Total number of chunks")
    total_size_bytes: int = Field(0, description="Total size in bytes")
    departments: Dict[str, int] = Field(default_factory=dict, description="Documents per department")
    services: Dict[str, int] = Field(default_factory=dict, description="Documents per service")


class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., description="Search query", min_length=1)
    top_k: int = Field(10, description="Number of results", ge=1, le=100)
    metadata_filter: Optional[Dict] = Field(None, description="Metadata filters")
    use_hybrid: bool = Field(True, description="Use hybrid search")


class SearchResult(BaseModel):
    """Search result model."""
    content: str = Field(..., description="Chunk content")
    metadata: Dict = Field(default_factory=dict, description="Chunk metadata")
    score: float = Field(..., description="Relevance score")


class SearchResponse(BaseModel):
    """Search response model."""
    query: str = Field(..., description="Original query")
    results: List[SearchResult] = Field(default_factory=list, description="Search results")
    total: int = Field(0, description="Total results found")


@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats() -> KnowledgeBaseStats:
    """
    Get knowledge base statistics.
    """
    doc_service = get_document_service()
    stats = doc_service.get_stats()

    return KnowledgeBaseStats(**stats)


@router.post("/search", response_model=SearchResponse)
async def search_knowledge_base(request: SearchRequest) -> SearchResponse:
    """
    Search the knowledge base.
    """
    try:
        logger.info(f"Searching knowledge base: {request.query}")

        rag_service = get_rag_service()

        # Initialize if needed
        if not rag_service._initialized:
            await rag_service.initialize()

            # Load documents
            doc_service = get_document_service()
            all_chunks = doc_service.get_all_chunks()
            if all_chunks:
                rag_service.add_documents(all_chunks)

        # Search
        if request.use_hybrid:
            results = rag_service._hybrid_search(request.query, top_k=request.top_k)
        else:
            results = rag_service._vector_search(request.query, top_k=request.top_k)

        # Apply metadata filter
        if request.metadata_filter:
            results = [
                r for r in results
                if all(
                    r.get("metadata", {}).get(k) == v
                    for k, v in request.metadata_filter.items()
                    if v
                )
            ]

        # Format results
        search_results = []
        for r in results:
            search_results.append(SearchResult(
                content=r.get("content", ""),
                metadata=r.get("metadata", {}),
                score=r.get("score", 0),
            ))

        return SearchResponse(
            query=request.query,
            results=search_results,
            total=len(search_results),
        )

    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex")
async def reindex_knowledge_base():
    """
    Reindex the entire knowledge base.
    """
    try:
        rag_service = get_rag_service()
        doc_service = get_document_service()

        # Clear existing index
        rag_service.clear_index()

        # Reload all documents
        all_chunks = doc_service.get_all_chunks()
        if all_chunks:
            await rag_service.initialize()
            rag_service.add_documents(all_chunks)

        return {
            "status": "completed",
            "message": f"Reindexed {len(all_chunks)} chunks",
        }

    except Exception as e:
        logger.error(f"Error reindexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_knowledge_base(confirm: bool = False):
    """
    Clear the entire knowledge base.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Please set confirm=true to clear the knowledge base"
        )

    rag_service = get_rag_service()
    rag_service.clear_index()

    return {
        "status": "cleared",
        "message": "Knowledge base has been cleared",
    }


@router.get("/departments")
async def list_departments() -> List[str]:
    """
    List all departments in the knowledge base.
    """
    doc_service = get_document_service()
    stats = doc_service.get_stats()
    return list(stats.get("departments", {}).keys())


@router.get("/services")
async def list_services() -> List[str]:
    """
    List all services in the knowledge base.
    """
    doc_service = get_document_service()
    stats = doc_service.get_stats()
    return list(stats.get("services", {}).keys())
