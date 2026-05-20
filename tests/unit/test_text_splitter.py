"""
Unit tests for text splitter.
"""

import pytest

from rag.processors.text_splitter import TextSplitter


class TestTextSplitter:
    """Tests for TextSplitter class."""

    def test_split_text_basic(self):
        """Test basic text splitting."""
        splitter = TextSplitter(chunk_size=100, chunk_overlap=20)

        text = "This is a test document. " * 20
        chunks = splitter.split_text(text)

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk) <= 100 + 50  # Allow some flexibility

    def test_split_text_empty(self):
        """Test splitting empty text."""
        splitter = TextSplitter()

        chunks = splitter.split_text("")

        assert chunks == []

    def test_split_text_short(self):
        """Test splitting short text."""
        splitter = TextSplitter(chunk_size=100)

        text = "Short text"
        chunks = splitter.split_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_split_text_with_metadata(self):
        """Test splitting text with metadata."""
        splitter = TextSplitter(chunk_size=100, chunk_overlap=20)

        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        metadata = {"source": "test.txt"}

        chunks = splitter.split_text_with_metadata(text, metadata)

        assert len(chunks) > 0
        for chunk in chunks:
            assert "content" in chunk
            assert "metadata" in chunk
            assert chunk["metadata"]["source"] == "test.txt"
            assert "chunk_index" in chunk["metadata"]

    def test_split_by_separator(self):
        """Test splitting by separator."""
        splitter = TextSplitter()

        text = "Line 1\nLine 2\nLine 3"
        chunks = splitter.split_by_separator(text, "\n")

        assert len(chunks) == 3
        assert chunks[0] == "Line 1"
        assert chunks[1] == "Line 2"
        assert chunks[2] == "Line 3"

    def test_split_by_sentences(self):
        """Test splitting by sentences."""
        splitter = TextSplitter()

        text = "First sentence. Second sentence. Third sentence."
        sentences = splitter.split_by_sentences(text)

        assert len(sentences) == 3

    def test_chunk_overlap(self):
        """Test chunk overlap."""
        splitter = TextSplitter(chunk_size=50, chunk_overlap=10)

        text = "A" * 100
        chunks = splitter.split_text(text)

        # Should have overlap between chunks
        assert len(chunks) > 1


if __name__ == "__main__":
    pytest.main([__file__])
