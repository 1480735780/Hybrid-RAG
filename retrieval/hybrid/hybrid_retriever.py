"""
Hybrid Retriever - Combining BM25 and Vector search for optimal retrieval.
"""

from typing import Dict, List, Optional

from loguru import logger


class HybridRetriever:
    """
    Hybrid Retriever combining BM25 and Vector search.

    Features:
    - BM25 keyword search
    - Vector semantic search
    - Score fusion
    - Configurable weights
    - Metadata filtering
    """

    def __init__(
        self,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
        top_k: int = 20,
        rerank_top_k: int = 5,
    ):
        """
        Initialize hybrid retriever.

        Args:
            bm25_weight: Weight for BM25 scores
            vector_weight: Weight for vector search scores
            top_k: Number of results to retrieve
            rerank_top_k: Number of results after reranking
        """
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.top_k = top_k
        self.rerank_top_k = rerank_top_k

        # Retrievers
        self._bm25_retriever = None
        self._vector_retriever = None

    def _get_bm25_retriever(self):
        """Get or create BM25 retriever."""
        if self._bm25_retriever is not None:
            return self._bm25_retriever

        from retrieval.bm25 import BM25Retriever

        self._bm25_retriever = BM25Retriever(top_k=self.top_k)
        return self._bm25_retriever

    def _get_vector_retriever(self):
        """Get or create vector retriever."""
        if self._vector_retriever is not None:
            return self._vector_retriever

        from retrieval.vector import VectorRetriever

        self._vector_retriever = VectorRetriever(top_k=self.top_k)
        return self._vector_retriever

    def build_index(
        self,
        documents: List[Dict],
        text_key: str = "content",
    ) -> None:
        """
        Build index for both BM25 and vector retrievers.

        Args:
            documents: List of documents with content and metadata
            text_key: Key for document text
        """
        logger.info(f"Building hybrid index with {len(documents)} documents")

        # Build BM25 index
        bm25_retriever = self._get_bm25_retriever()
        bm25_retriever.build_index(documents, text_key)

        # Build vector index
        vector_retriever = self._get_vector_retriever()
        vector_retriever.add_documents(documents, text_key)

        logger.info("Hybrid index built successfully")

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict] = None,
        use_hybrid: bool = True,
    ) -> List[Dict]:
        """
        Search documents using hybrid retrieval.

        Args:
            query: Search query
            top_k: Number of results to return
            metadata_filter: Metadata filters
            use_hybrid: Use hybrid search (BM25 + Vector)

        Returns:
            List of search results with scores
        """
        top_k = top_k or self.rerank_top_k

        if use_hybrid:
            return self._hybrid_search(query, top_k, metadata_filter)
        else:
            return self._vector_search(query, top_k, metadata_filter)

    def _hybrid_search(
        self,
        query: str,
        top_k: int,
        metadata_filter: Optional[Dict],
    ) -> List[Dict]:
        """
        Perform hybrid search combining BM25 and vector search.

        Args:
            query: Search query
            top_k: Number of results to return
            metadata_filter: Metadata filters

        Returns:
            List of search results with scores
        """
        # Get BM25 results
        bm25_retriever = self._get_bm25_retriever()
        bm25_results = bm25_retriever.search(
            query=query,
            top_k=self.top_k,
            metadata_filter=metadata_filter,
        )

        # Get vector results
        vector_retriever = self._get_vector_retriever()
        vector_results = vector_retriever.search(
            query=query,
            top_k=self.top_k,
            metadata_filter=metadata_filter,
        )

        # Fuse scores
        fused_results = self._fuse_scores(bm25_results, vector_results)

        # Sort by score and return top-k
        fused_results.sort(key=lambda x: x["score"], reverse=True)

        return fused_results[:top_k]

    def _vector_search(
        self,
        query: str,
        top_k: int,
        metadata_filter: Optional[Dict],
    ) -> List[Dict]:
        """
        Perform vector search only.

        Args:
            query: Search query
            top_k: Number of results to return
            metadata_filter: Metadata filters

        Returns:
            List of search results with scores
        """
        vector_retriever = self._get_vector_retriever()
        return vector_retriever.search(
            query=query,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )

    def _fuse_scores(
        self,
        bm25_results: List[Dict],
        vector_results: List[Dict],
    ) -> List[Dict]:
        """
        Fuse BM25 and vector search scores.

        Args:
            bm25_results: BM25 search results
            vector_results: Vector search results

        Returns:
            Fused results with combined scores
        """
        # Create score maps
        bm25_scores = {}
        for result in bm25_results:
            content_hash = hash(result["content"])
            bm25_scores[content_hash] = result

        vector_scores = {}
        for result in vector_results:
            content_hash = hash(result["content"])
            vector_scores[content_hash] = result

        # Normalize scores
        bm25_max = max([r["score"] for r in bm25_results], default=1.0)
        vector_max = max([r["score"] for r in vector_results], default=1.0)

        # Fuse scores
        all_hashes = set(bm25_scores.keys()) | set(vector_scores.keys())
        fused_results = []

        for content_hash in all_hashes:
            bm25_score = bm25_scores.get(content_hash, {}).get("score", 0) / bm25_max
            vector_score = vector_scores.get(content_hash, {}).get("score", 0) / vector_max

            # Weighted sum
            fused_score = (
                self.bm25_weight * bm25_score +
                self.vector_weight * vector_score
            )

            # Get result from either source
            result = bm25_scores.get(content_hash) or vector_scores.get(content_hash)
            result["score"] = fused_score
            result["bm25_score"] = bm25_score
            result["vector_score"] = vector_score

            fused_results.append(result)

        return fused_results

    def add_documents(
        self,
        documents: List[Dict],
        text_key: str = "content",
    ) -> None:
        """
        Add documents to both retrievers.

        Args:
            documents: List of documents to add
            text_key: Key for document text
        """
        bm25_retriever = self._get_bm25_retriever()
        bm25_retriever.add_documents(documents, text_key)

        vector_retriever = self._get_vector_retriever()
        vector_retriever.add_documents(documents, text_key)

        logger.info(f"Added {len(documents)} documents to hybrid index")

    def get_document_count(self) -> Dict[str, int]:
        """
        Get document counts from both retrievers.

        Returns:
            Dict with BM25 and vector document counts
        """
        bm25_retriever = self._get_bm25_retriever()
        vector_retriever = self._get_vector_retriever()

        return {
            "bm25": bm25_retriever.get_document_count(),
            "vector": vector_retriever.get_document_count(),
        }
