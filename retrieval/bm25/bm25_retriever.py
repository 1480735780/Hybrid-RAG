"""
BM25 Retriever - Keyword-based retrieval for Hybrid RAG.
"""

from typing import Dict, List, Optional

import numpy as np
from loguru import logger


class BM25Retriever:
    """
    BM25 Retriever for keyword-based document retrieval.

    Features:
    - Chinese text support (jieba)
    - Configurable BM25 parameters
    - Metadata filtering
    - Efficient indexing
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        top_k: int = 20,
    ):
        """
        Initialize BM25 retriever.

        Args:
            k1: Term frequency saturation parameter
            b: Document length normalization parameter
            top_k: Number of results to return
        """
        self.k1 = k1
        self.b = b
        self.top_k = top_k

        # BM25 index
        self._bm25 = None
        self._documents = []
        self._tokenized_docs = []
        self._doc_metadata = []

        # Chinese tokenizer
        self._tokenizer = None

    def _get_tokenizer(self):
        """Get or create Chinese tokenizer."""
        if self._tokenizer is not None:
            return self._tokenizer

        try:
            import jieba
            self._tokenizer = jieba
            return self._tokenizer
        except ImportError:
            logger.warning("jieba not installed, using simple tokenizer")
            return None

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        tokenizer = self._get_tokenizer()

        if tokenizer:
            # Use jieba for Chinese tokenization
            return list(tokenizer.cut(text))
        else:
            # Simple tokenization (split by whitespace and punctuation)
            import re
            tokens = re.findall(r'[\w一-鿿]+', text.lower())
            return tokens

    def build_index(
        self,
        documents: List[Dict],
        text_key: str = "content",
    ) -> None:
        """
        Build BM25 index from documents.

        Args:
            documents: List of documents with content and metadata
            text_key: Key for document text
        """
        logger.info(f"Building BM25 index with {len(documents)} documents")

        self._documents = documents
        self._doc_metadata = [doc.get("metadata", {}) for doc in documents]

        # Tokenize documents
        self._tokenized_docs = []
        for doc in documents:
            text = doc.get(text_key, "")
            tokens = self._tokenize(text)
            self._tokenized_docs.append(tokens)

        # Build BM25 index
        from rank_bm25 import BM25Okapi

        self._bm25 = BM25Okapi(
            self._tokenized_docs,
            k1=self.k1,
            b=self.b,
        )

        logger.info("BM25 index built successfully")

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Search documents using BM25.

        Args:
            query: Search query
            top_k: Number of results to return
            metadata_filter: Metadata filters

        Returns:
            List of search results with scores
        """
        if self._bm25 is None:
            logger.warning("BM25 index not built")
            return []

        top_k = top_k or self.top_k

        # Tokenize query
        query_tokens = self._tokenize(query)

        # Get BM25 scores
        scores = self._bm25.get_scores(query_tokens)

        # Apply metadata filter
        if metadata_filter:
            filtered_indices = self._apply_metadata_filter(metadata_filter)
            scores = [scores[i] if i in filtered_indices else 0 for i in range(len(scores))]

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Build results
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "content": self._documents[idx].get("content", ""),
                    "metadata": self._doc_metadata[idx],
                    "score": float(scores[idx]),
                    "index": int(idx),
                })

        return results

    def _apply_metadata_filter(self, metadata_filter: Dict) -> set:
        """
        Apply metadata filter to get matching document indices.

        Args:
            metadata_filter: Metadata filters

        Returns:
            Set of matching document indices
        """
        matching_indices = set()

        for idx, metadata in enumerate(self._doc_metadata):
            match = True
            for key, value in metadata_filter.items():
                if key not in metadata or metadata[key] != value:
                    match = False
                    break
            if match:
                matching_indices.add(idx)

        return matching_indices

    def add_documents(
        self,
        documents: List[Dict],
        text_key: str = "content",
    ) -> None:
        """
        Add documents to existing index.

        Args:
            documents: List of documents to add
            text_key: Key for document text
        """
        for doc in documents:
            text = doc.get(text_key, "")
            tokens = self._tokenize(text)

            self._documents.append(doc)
            self._tokenized_docs.append(tokens)
            self._doc_metadata.append(doc.get("metadata", {}))

        # Rebuild index
        from rank_bm25 import BM25Okapi

        self._bm25 = BM25Okapi(
            self._tokenized_docs,
            k1=self.k1,
            b=self.b,
        )

        logger.info(f"Added {len(documents)} documents to BM25 index")

    def remove_documents(self, indices: List[int]) -> None:
        """
        Remove documents from index by indices.

        Args:
            indices: List of document indices to remove
        """
        # Remove in reverse order to maintain correct indices
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self._documents):
                self._documents.pop(idx)
                self._tokenized_docs.pop(idx)
                self._doc_metadata.pop(idx)

        # Rebuild index
        from rank_bm25 import BM25Okapi

        self._bm25 = BM25Okapi(
            self._tokenized_docs,
            k1=self.k1,
            b=self.b,
        )

        logger.info(f"Removed {len(indices)} documents from BM25 index")

    def get_document_count(self) -> int:
        """
        Get number of documents in index.

        Returns:
            Number of documents
        """
        return len(self._documents)
