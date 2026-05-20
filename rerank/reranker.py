"""
Reranker - Document reranking using BGE-Reranker.
"""

from typing import Dict, List, Optional

from loguru import logger


class Reranker:
    """
    Reranker for document reranking using BGE-Reranker.

    Features:
    - BGE-Reranker support
    - Cross-encoder scoring
    - Configurable top-k
    - Batch processing
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        device: str = "cpu",
        top_k: int = 3,
    ):
        """
        Initialize reranker.

        Args:
            model_name: Reranker model name
            device: Device to use (cpu, cuda, auto)
            top_k: Number of results to return after reranking
        """
        self.model_name = model_name
        self.device = device
        self.top_k = top_k

        # Model
        self._model = None

    def _load_model(self) -> None:
        """Load the reranker model."""
        if self._model is not None:
            return

        logger.info(f"Loading reranker model: {self.model_name}")

        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(
                self.model_name,
                max_length=512,
                device=self.device,
            )

            logger.info(f"Reranker model loaded successfully on {self.device}")

        except ImportError:
            logger.error("sentence-transformers not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            raise

    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: Optional[int] = None,
    ) -> List[Dict]:
        """
        Rerank documents based on query relevance.

        Args:
            query: Search query
            documents: List of documents to rerank
            top_k: Number of results to return

        Returns:
            List of reranked documents
        """
        if not documents:
            return []

        self._load_model()

        top_k = top_k or self.top_k

        # Prepare query-document pairs
        pairs = [(query, doc.get("content", "")) for doc in documents]

        # Get reranker scores
        scores = self._model.predict(pairs)

        # Add scores to documents
        for i, doc in enumerate(documents):
            doc["rerank_score"] = float(scores[i])

        # Sort by reranker score
        reranked_docs = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)

        # Return top-k
        return reranked_docs[:top_k]

    def rerank_with_batch(
        self,
        queries: List[str],
        documents_list: List[List[Dict]],
        top_k: Optional[int] = None,
    ) -> List[List[Dict]]:
        """
        Rerank multiple query-document sets in batch.

        Args:
            queries: List of queries
            documents_list: List of document lists
            top_k: Number of results to return per query

        Returns:
            List of reranked document lists
        """
        self._load_model()

        top_k = top_k or self.top_k

        all_results = []

        for query, documents in zip(queries, documents_list):
            if not documents:
                all_results.append([])
                continue

            # Prepare query-document pairs
            pairs = [(query, doc.get("content", "")) for doc in documents]

            # Get reranker scores
            scores = self._model.predict(pairs)

            # Add scores to documents
            for i, doc in enumerate(documents):
                doc["rerank_score"] = float(scores[i])

            # Sort by reranker score
            reranked_docs = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)

            # Return top-k
            all_results.append(reranked_docs[:top_k])

        return all_results

    def compute_scores(
        self,
        query: str,
        documents: List[Dict],
    ) -> List[float]:
        """
        Compute reranker scores for documents.

        Args:
            query: Search query
            documents: List of documents

        Returns:
            List of scores
        """
        self._load_model()

        # Prepare query-document pairs
        pairs = [(query, doc.get("content", "")) for doc in documents]

        # Get reranker scores
        scores = self._model.predict(pairs)

        return scores.tolist()

    def filter_by_threshold(
        self,
        documents: List[Dict],
        threshold: float = 0.5,
    ) -> List[Dict]:
        """
        Filter documents by reranker score threshold.

        Args:
            documents: List of documents with reranker scores
            threshold: Minimum score threshold

        Returns:
            Filtered documents
        """
        return [
            doc for doc in documents
            if doc.get("rerank_score", 0) >= threshold
        ]
