"""
Integration tests for RAG pipeline.
"""

import pytest

from rag.processors.text_splitter import TextSplitter
from rag.processors.text_cleaner import TextCleaner


class TestRAGPipeline:
    """Integration tests for RAG pipeline components."""

    def test_text_processing_pipeline(self):
        """Test text processing pipeline."""
        # Sample text
        text = """
        MySQL Troubleshooting Guide

        1. Connection Issues

        If you encounter "ERROR 2002 (HY000): Can't connect to local MySQL server",
        check the following:

        - Is MySQL service running?
        - Check MySQL socket file
        - Verify MySQL configuration

        2. Performance Issues

        For slow queries, consider:
        - Enable slow query log
        - Analyze query execution plan
        - Optimize indexes
        """

        # Clean text
        cleaner = TextCleaner()
        cleaned_text = cleaner.clean(text)

        # Split text
        splitter = TextSplitter(chunk_size=200, chunk_overlap=50)
        chunks = splitter.split_text(cleaned_text)

        # Verify
        assert len(chunks) > 0
        assert all(len(chunk) > 0 for chunk in chunks)

    def test_metadata_extraction(self):
        """Test metadata extraction."""
        text = "Docker container failed to start. Check logs for details."

        cleaner = TextCleaner()
        errors = cleaner.extract_error_messages(text)

        # Should not crash even if no errors found
        assert isinstance(errors, list)

    def test_chunk_metadata(self):
        """Test chunk metadata generation."""
        splitter = TextSplitter(chunk_size=100, chunk_overlap=20)

        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        metadata = {"source": "test.md", "department": "ops"}

        chunks = splitter.split_text_with_metadata(text, metadata)

        for chunk in chunks:
            assert "content" in chunk
            assert "metadata" in chunk
            assert chunk["metadata"]["source"] == "test.md"
            assert chunk["metadata"]["department"] == "ops"
            assert "chunk_index" in chunk["metadata"]
            assert "start_char" in chunk["metadata"]
            assert "end_char" in chunk["metadata"]


if __name__ == "__main__":
    pytest.main([__file__])
