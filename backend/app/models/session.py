"""
Chat session database models.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from backend.app.models.document import Base


class ChatSession(Base):
    """Chat session model for storing conversation sessions."""

    __tablename__ = "chat_sessions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), nullable=True, index=True)
    title = Column(String(255), nullable=True)

    # Session metadata
    metadata_filter = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id})>"


class ChatMessage(Base):
    """Chat message model for storing conversation messages."""

    __tablename__ = "chat_messages"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False, index=True)

    # Message content
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # RAG metadata
    sources = Column(JSON, nullable=True)  # Source documents used
    query = Column(Text, nullable=True)  # Original query
    rewritten_query = Column(Text, nullable=True)  # Rewritten query

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role={self.role})>"
