"""
Markdown Parser - Extract text from Markdown files.
"""

from pathlib import Path
from typing import Dict

from loguru import logger

from rag.parsers.document_parser import BaseParser


class MarkdownParser(BaseParser):
    """
    Markdown Parser for extracting text from Markdown files.

    Features:
    - Heading extraction
    - Code block preservation
    - Metadata extraction (frontmatter)
    """

    def parse(self, file_path: str) -> str:
        """
        Parse Markdown file and return content.

        Args:
            file_path: Path to the Markdown file

        Returns:
            Extracted text content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Remove frontmatter if present
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2].strip()

            return content

        except Exception as e:
            logger.error(f"Error parsing Markdown file: {e}")
            raise

    def parse_with_metadata(self, file_path: str) -> Dict:
        """
        Parse Markdown file and return content with metadata.

        Args:
            file_path: Path to the Markdown file

        Returns:
            Dict with text and metadata
        """
        try:
            path = Path(file_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract frontmatter
            frontmatter = {}
            text = content

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1].strip()
                    text = parts[2].strip()

                    # Parse frontmatter (simple key-value pairs)
                    for line in frontmatter_text.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            frontmatter[key.strip()] = value.strip()

            # Extract headings
            headings = []
            for line in text.split('\n'):
                if line.startswith('#'):
                    level = len(line.split(' ')[0])
                    heading = line.lstrip('#').strip()
                    headings.append({
                        "level": level,
                        "text": heading,
                    })

            metadata = {
                "file_path": file_path,
                "file_type": "md",
                "filename": path.name,
                "file_size": path.stat().st_size,
                "frontmatter": frontmatter,
                "headings": headings,
                "total_headings": len(headings),
            }

            return {
                "text": text,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Error parsing Markdown file with metadata: {e}")
            raise
