"""
Document Service - Document processing and management.
Real implementation with file parsing and chunking.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from loguru import logger

from backend.config.settings import Settings, get_settings


class DocumentService:
    """
    Document Service for processing and managing documents.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

        # Storage
        self._documents = {}  # document_id -> document_info
        self._chunks = {}     # document_id -> list of chunks

        # Upload directory
        self.upload_dir = Path("knowledge_base/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Process a document."""
        document_id = str(uuid4())
        logger.info(f"Processing document: {filename} (ID: {document_id})")

        try:
            # Save file
            file_path = self.upload_dir / f"{document_id}_{filename}"
            with open(file_path, "wb") as f:
                f.write(file_content)

            # Parse document
            text = self._parse_file(file_path, filename)

            # Clean text
            cleaned_text = self._clean_text(text)

            # Split into chunks
            chunks = self._split_text(cleaned_text, metadata)

            # Store document info
            doc_info = {
                "document_id": document_id,
                "filename": filename,
                "file_size": len(file_content),
                "file_type": Path(filename).suffix,
                "status": "completed",
                "metadata": metadata or {},
                "chunks_count": len(chunks),
                "file_path": str(file_path),
            }

            self._documents[document_id] = doc_info
            self._chunks[document_id] = chunks

            logger.info(f"Document processed: {filename}, {len(chunks)} chunks")

            return doc_info

        except Exception as e:
            logger.error(f"Failed to process document: {e}")
            return {
                "document_id": document_id,
                "filename": filename,
                "status": "failed",
                "error": str(e),
            }

    def _parse_file(self, file_path: Path, filename: str) -> str:
        """Parse file based on type."""
        suffix = Path(filename).suffix.lower()

        if suffix == ".txt" or suffix == ".log":
            return self._parse_text(file_path)
        elif suffix == ".md":
            return self._parse_markdown(file_path)
        elif suffix == ".pdf":
            return self._parse_pdf(file_path)
        elif suffix == ".docx":
            return self._parse_docx(file_path)
        else:
            # Try as text
            return self._parse_text(file_path)

    def _parse_text(self, file_path: Path) -> str:
        """Parse text file."""
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        with open(file_path, 'rb') as f:
            return f.read().decode('utf-8', errors='replace')

    def _parse_markdown(self, file_path: Path) -> str:
        """Parse markdown file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].strip()

        return content

    def _parse_pdf(self, file_path: Path) -> str:
        """Parse PDF file."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(file_path))
            text_parts = []

            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"[第{page_num + 1}页]\n{page_text}")

            return "\n\n".join(text_parts)

        except ImportError:
            logger.warning("pypdf not installed, cannot parse PDF")
            return f"[PDF file: {file_path.name}]"

        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")
            return f"[PDF parse error: {e}]"

    def _parse_docx(self, file_path: Path) -> str:
        """Parse DOCX file."""
        try:
            from docx import Document

            doc = Document(str(file_path))
            text_parts = []

            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)

            return "\n\n".join(text_parts)

        except ImportError:
            logger.warning("python-docx not installed, cannot parse DOCX")
            return f"[DOCX file: {file_path.name}]"

        except Exception as e:
            logger.error(f"Failed to parse DOCX: {e}")
            return f"[DOCX parse error: {e}]"

    def _clean_text(self, text: str) -> str:
        """Clean text."""
        import re

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)

        return text.strip()

    def _split_text(
        self,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> List[Dict]:
        """Split text into chunks."""
        chunk_size = self.settings.CHUNK_SIZE
        chunk_overlap = self.settings.CHUNK_OVERLAP

        chunks = []

        # Split by paragraphs first
        paragraphs = text.split('\n\n')

        current_chunk = ""
        current_pos = 0

        for para in paragraphs:
            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(para) > chunk_size:
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": {
                            **(metadata or {}),
                            "chunk_index": len(chunks),
                            "start_char": current_pos,
                            "end_char": current_pos + len(current_chunk),
                        },
                    })

                    # Keep overlap
                    overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else ""
                    current_pos += len(current_chunk) - len(overlap_text)
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para
            else:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para

        # Add last chunk
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "metadata": {
                    **(metadata or {}),
                    "chunk_index": len(chunks),
                    "start_char": current_pos,
                    "end_char": current_pos + len(current_chunk),
                },
            })

        return chunks

    def get_document(self, document_id: str) -> Optional[Dict]:
        """Get document by ID."""
        return self._documents.get(document_id)

    def get_all_documents(self) -> List[Dict]:
        """Get all documents."""
        return list(self._documents.values())

    def get_chunks(self, document_id: str) -> List[Dict]:
        """Get chunks for a document."""
        return self._chunks.get(document_id, [])

    def get_all_chunks(self) -> List[Dict]:
        """Get all chunks from all documents."""
        all_chunks = []
        for chunks in self._chunks.values():
            all_chunks.extend(chunks)
        return all_chunks

    def delete_document(self, document_id: str) -> bool:
        """Delete a document."""
        if document_id in self._documents:
            doc = self._documents[document_id]

            # Delete file
            file_path = doc.get("file_path")
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

            # Remove from storage
            del self._documents[document_id]
            if document_id in self._chunks:
                del self._chunks[document_id]

            logger.info(f"Document deleted: {document_id}")
            return True

        return False

    def get_stats(self) -> Dict:
        """Get knowledge base statistics."""
        total_chunks = sum(len(chunks) for chunks in self._chunks.values())
        total_size = sum(doc.get("file_size", 0) for doc in self._documents.values())

        departments = {}
        services = {}

        for doc in self._documents.values():
            dept = doc.get("metadata", {}).get("department", "unknown")
            svc = doc.get("metadata", {}).get("service", "unknown")

            departments[dept] = departments.get(dept, 0) + 1
            services[svc] = services.get(svc, 0) + 1

        return {
            "total_documents": len(self._documents),
            "total_chunks": total_chunks,
            "total_size_bytes": total_size,
            "departments": departments,
            "services": services,
        }
