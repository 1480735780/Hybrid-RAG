"""
Document database models.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """SQLAlchemy base class."""
    pass


class Document(Base):
    """Document model for storing document metadata."""

    __tablename__ = "documents"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    filename = Column(String(255), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    status = Column(String(50), default="processing")  # processing, completed, failed

    # Metadata
    department = Column(String(100), index=True)
    service = Column(String(100), index=True)
    level = Column(String(20))
    tags = Column(JSON, default=list)
    source = Column(String(255))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename})>"


class DocumentChunk(Base):
    """Document chunk model for storing text chunks."""

    __tablename__ = "document_chunks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(PGUUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)

    # Content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)

    # Metadata
    page_number = Column(Integer, nullable=True)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)

    # Vector store reference
    vector_id = Column(String(255), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"
