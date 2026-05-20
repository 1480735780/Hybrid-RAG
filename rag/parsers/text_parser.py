"""
Text Parser - Extract text from plain text files.
"""

from pathlib import Path
from typing import Dict

from loguru import logger

from rag.parsers.document_parser import BaseParser


class TextParser(BaseParser):
    """
    Text Parser for extracting text from plain text files.

    Features:
    - Encoding detection
    - Line-by-line extraction
    - Metadata extraction
    """

    def parse(self, file_path: str) -> str:
        """
        Parse text file and return content.

        Args:
            file_path: Path to the text file

        Returns:
            Extracted text content
        """
        try:
            # Try different encodings
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue

            # If all encodings fail, read as binary and decode with errors='replace'
            with open(file_path, 'rb') as f:
                return f.read().decode('utf-8', errors='replace')

        except Exception as e:
            logger.error(f"Error parsing text file: {e}")
            raise

    def parse_with_metadata(self, file_path: str) -> Dict:
        """
        Parse text file and return content with metadata.

        Args:
            file_path: Path to the text file

        Returns:
            Dict with text and metadata
        """
        try:
            path = Path(file_path)
            text = self.parse(file_path)

            # Count lines and characters
            lines = text.split('\n')

            metadata = {
                "file_path": file_path,
                "file_type": "txt",
                "filename": path.name,
                "file_size": path.stat().st_size,
                "total_lines": len(lines),
                "total_chars": len(text),
                "encoding": "utf-8",
            }

            return {
                "text": text,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Error parsing text file with metadata: {e}")
            raise
