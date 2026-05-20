"""
Document management endpoints.
"""

import json
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from loguru import logger

router = APIRouter()

# Global services
_document_service = None
_rag_service = None


def get_document_service():
    """Get or create document service."""
    global _document_service
    if _document_service is None:
        from backend.app.services.document_service import DocumentService
        _document_service = DocumentService()
    return _document_service


def get_rag_service():
    """Get or create RAG service."""
    global _rag_service
    if _rag_service is None:
        from backend.app.services.rag_service import RAGService
        _rag_service = RAGService()
    return _rag_service


# Request/Response Models
class DocumentMetadata(BaseModel):
    """Document metadata model."""
    department: Optional[str] = Field(None, description="Department: ops, dev, security")
    service: Optional[str] = Field(None, description="Service name: mysql, docker, nginx")
    level: Optional[str] = Field(None, description="Priority level: P1, P2, P3")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    source: Optional[str] = Field(None, description="Document source")


class DocumentUploadResponse(BaseModel):
    """Document upload response model."""
    document_id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    chunks_count: int = Field(..., description="Number of chunks created")
    status: str = Field(..., description="Processing status")
    metadata: dict = Field(default_factory=dict, description="Document metadata")


class DocumentListResponse(BaseModel):
    """Document list response model."""
    total: int
    documents: List[dict]


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
) -> DocumentUploadResponse:
    """
    Upload and process a document for knowledge base.
    """
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)

        # Parse metadata
        doc_metadata = {}
        if metadata:
            try:
                doc_metadata = json.loads(metadata)
            except:
                doc_metadata = {}

        # Validate file size (max 50MB)
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds 50MB limit"
            )

        # Validate file extension
        allowed_extensions = {".pdf", ".docx", ".txt", ".md", ".log"}
        file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
            )

        logger.info(f"Uploading document: {file.filename}")

        # Get document service
        doc_service = get_document_service()

        # Process document
        result = await doc_service.process_document(
            file_content=content,
            filename=file.filename,
            metadata=doc_metadata,
        )

        # Add to RAG index
        if result.get("status") == "completed":
            rag_service = get_rag_service()
            chunks = doc_service.get_chunks(result["document_id"])

            if chunks:
                await rag_service.initialize()
                rag_service.add_documents(chunks)
                logger.info(f"Added {len(chunks)} chunks to RAG index")

        return DocumentUploadResponse(
            document_id=result["document_id"],
            filename=file.filename,
            file_size=file_size,
            chunks_count=result.get("chunks_count", 0),
            status=result.get("status", "processing"),
            metadata=doc_metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    department: Optional[str] = None,
    service: Optional[str] = None,
) -> DocumentListResponse:
    """
    List all documents in the knowledge base.
    """
    doc_service = get_document_service()
    documents = doc_service.get_all_documents()

    # Apply filters
    if department:
        documents = [d for d in documents if d.get("metadata", {}).get("department") == department]
    if service:
        documents = [d for d in documents if d.get("metadata", {}).get("service") == service]

    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated = documents[start:end]

    return DocumentListResponse(
        total=len(documents),
        documents=paginated,
    )


@router.get("/{document_id}")
async def get_document(document_id: str):
    """
    Get document information by ID.
    """
    doc_service = get_document_service()
    doc = doc_service.get_document(document_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return doc


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from the knowledge base.
    """
    doc_service = get_document_service()

    if doc_service.delete_document(document_id):
        return {"status": "deleted", "document_id": document_id}

    raise HTTPException(status_code=404, detail="Document not found")
