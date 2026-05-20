"""
Text Splitter - Split text into chunks for RAG processing.
"""

from typing import Dict, List, Optional

from loguru import logger


class TextSplitter:
    """
    Text Splitter for splitting text into chunks.

    Features:
    - Configurable chunk size and overlap
    - Multiple splitting strategies
    - Metadata preservation
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        length_function: str = "len",
    ):
        """
        Initialize text splitter.

        Args:
            chunk_size: Maximum chunk size
            chunk_overlap: Overlap between chunks
            length_function: Function to calculate length (len or tokens)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function

    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        if not text:
            return []

        # Split by paragraphs first
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = []

        for paragraph in paragraphs:
            # If adding this paragraph exceeds chunk size, save current chunk
            if self._get_length('\n\n'.join(current_chunk + [paragraph])) > self.chunk_size:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    # Keep overlap
                    current_chunk = current_chunk[-self._get_overlap_count(current_chunk):]

            current_chunk.append(paragraph)

        # Add last chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def split_text_with_metadata(
        self,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Split text into chunks with metadata.

        Args:
            text: Text to split
            metadata: Base metadata to include

        Returns:
            List of chunks with metadata
        """
        chunks = self.split_text(text)

        result = []
        current_pos = 0

        for i, chunk in enumerate(chunks):
            # Find position in original text
            start_pos = text.find(chunk, current_pos)
            if start_pos == -1:
                start_pos = current_pos
            end_pos = start_pos + len(chunk)

            chunk_metadata = {
                **(metadata or {}),
                "chunk_index": i,
                "start_char": start_pos,
                "end_char": end_pos,
                "char_count": len(chunk),
            }

            result.append({
                "content": chunk,
                "metadata": chunk_metadata,
            })

            current_pos = end_pos - self.chunk_overlap

        return result

    def _get_length(self, text: str) -> int:
        """
        Get length of text based on length function.

        Args:
            text: Text to measure

        Returns:
            Length of text
        """
        if self.length_function == "tokens":
            # TODO: Implement token counting
            return len(text.split())
        return len(text)

    def _get_overlap_count(self, chunks: List[str]) -> int:
        """
        Get number of chunks to keep for overlap.

        Args:
            chunks: Current chunks

        Returns:
            Number of chunks to keep
        """
        if not chunks:
            return 0

        total_length = 0
        count = 0

        for chunk in reversed(chunks):
            total_length += len(chunk)
            count += 1
            if total_length >= self.chunk_overlap:
                break

        return count

    def split_by_separator(
        self,
        text: str,
        separator: str = "\n",
    ) -> List[str]:
        """
        Split text by separator.

        Args:
            text: Text to split
            separator: Separator string

        Returns:
            List of text chunks
        """
        return text.split(separator)

    def split_by_sentences(self, text: str) -> List[str]:
        """
        Split text by sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        import re

        # Split by sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Clean sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def split_by_tokens(self, text: str) -> List[str]:
        """
        Split text by tokens (words).

        Args:
            text: Text to split

        Returns:
            List of token chunks
        """
        words = text.split()

        chunks = []
        current_chunk = []

        for word in words:
            if len(current_chunk) + 1 > self.chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = current_chunk[-self.chunk_overlap:]

            current_chunk.append(word)

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks
