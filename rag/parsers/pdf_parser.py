"""
PDF Parser - Extract text from PDF documents.
"""

from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from rag.parsers.document_parser import BaseParser


class PDFParser(BaseParser):
    """
    PDF Parser for extracting text from PDF documents.

    Features:
    - Page-by-page extraction
    - Metadata extraction
    - Text cleaning
    """

    def parse(self, file_path: str) -> str:
        """
        Parse PDF and return text content.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text content
        """
        try:
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            text_parts = []

            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"[Page {page_num + 1}]\n{page_text}")

            return "\n\n".join(text_parts)

        except ImportError:
            logger.warning("pypdf not installed, trying PyPDF2")
            return self._parse_with_pypdf2(file_path)
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise

    def _parse_with_pypdf2(self, file_path: str) -> str:
        """Fallback parser using PyPDF2."""
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(file_path)
            text_parts = []

            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"[Page {page_num + 1}]\n{page_text}")

            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"Error parsing PDF with PyPDF2: {e}")
            raise

    def parse_with_metadata(self, file_path: str) -> Dict:
        """
        Parse PDF and return text with metadata.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dict with text and metadata
        """
        try:
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            text_parts = []
            pages = []

            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"[Page {page_num + 1}]\n{page_text}")
                    pages.append({
                        "page_number": page_num + 1,
                        "text": page_text,
                        "char_count": len(page_text),
                    })

            # Extract PDF metadata
            metadata = {
                "file_path": file_path,
                "file_type": "pdf",
                "total_pages": len(reader.pages),
                "pages": pages,
            }

            # Add PDF metadata if available
            if reader.metadata:
                metadata.update({
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "subject": reader.metadata.get("/Subject", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                })

            return {
                "text": "\n\n".join(text_parts),
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Error parsing PDF with metadata: {e}")
            raise
