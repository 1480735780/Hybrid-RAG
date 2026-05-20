"""
Document Parser - Base class and factory for document parsing.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger


class BaseParser(ABC):
    """Base class for document parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> str:
        """
        Parse document and return text content.

        Args:
            file_path: Path to the document

        Returns:
            Extracted text content
        """
        pass

    @abstractmethod
    def parse_with_metadata(self, file_path: str) -> Dict:
        """
        Parse document and return text with metadata.

        Args:
            file_path: Path to the document

        Returns:
            Dict with text and metadata
        """
        pass


class DocumentParser:
    """
    Document Parser - Factory for creating appropriate parsers.

    Supported formats:
    - PDF
    - DOCX
    - TXT
    - Markdown
    - Log files
    """

    def __init__(self):
        """Initialize document parser with all supported parsers."""
        self._parsers = {
            ".pdf": PDFParser(),
            ".docx": DocxParser(),
            ".txt": TextParser(),
            ".md": MarkdownParser(),
            ".log": LogParser(),
        }

    def get_parser(self, file_extension: str) -> Optional[BaseParser]:
        """
        Get parser for file extension.

        Args:
            file_extension: File extension (e.g., .pdf)

        Returns:
            Parser instance or None
        """
        return self._parsers.get(file_extension.lower())

    def parse(self, file_path: str) -> str:
        """
        Parse document based on file extension.

        Args:
            file_path: Path to the document

        Returns:
            Extracted text content

        Raises:
            ValueError: If file type is not supported
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        parser = self.get_parser(extension)
        if parser is None:
            raise ValueError(f"Unsupported file type: {extension}")

        logger.info(f"Parsing document: {path.name}")
        return parser.parse(file_path)

    def parse_with_metadata(self, file_path: str) -> Dict:
        """
        Parse document and return text with metadata.

        Args:
            file_path: Path to the document

        Returns:
            Dict with text and metadata
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        parser = self.get_parser(extension)
        if parser is None:
            raise ValueError(f"Unsupported file type: {extension}")

        logger.info(f"Parsing document with metadata: {path.name}")
        return parser.parse_with_metadata(file_path)

    def is_supported(self, file_path: str) -> bool:
        """
        Check if file type is supported.

        Args:
            file_path: Path to the document

        Returns:
            True if supported, False otherwise
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        return extension in self._parsers

    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions.

        Returns:
            List of supported extensions
        """
        return list(self._parsers.keys())
