"""
Embedding Model - BGE-M3 implementation for text embeddings.
"""

from typing import List, Optional

import numpy as np
from loguru import logger


class EmbeddingModel:
    """
    Embedding Model using BGE-M3 for generating text embeddings.

    BGE-M3 Features:
    - Multi-lingual support
    - Multi-granularity (dense, sparse, colbert)
    - High performance on Chinese and English texts
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = "cpu",
        batch_size: int = 32,
        normalize: bool = True,
    ):
        """
        Initialize embedding model.

        Args:
            model_name: Model name or path
            device: Device to use (cpu, cuda, auto)
            batch_size: Batch size for encoding
            normalize: Whether to normalize embeddings
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.normalize = normalize
        self._model = None

    def _load_model(self) -> None:
        """Load the embedding model."""
        if self._model is not None:
            return

        logger.info(f"Loading embedding model: {self.model_name}")

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
            )

            logger.info(f"Embedding model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def encode(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of texts to encode
            batch_size: Batch size (overrides default)
            show_progress: Whether to show progress bar

        Returns:
            numpy array of embeddings
        """
        self._load_model()

        batch_size = batch_size or self.batch_size

        logger.debug(f"Encoding {len(texts)} texts with batch size {batch_size}")

        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=self.normalize,
        )

        return embeddings

    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a single query string.

        Args:
            query: Query text

        Returns:
            numpy array embedding
        """
        return self.encode([query])[0]

    def encode_documents(self, documents: List[str]) -> np.ndarray:
        """
        Encode a list of documents.

        Args:
            documents: List of document texts

        Returns:
            numpy array of embeddings
        """
        return self.encode(documents)

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Cosine similarity score
        """
        return float(np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        ))

    def batch_similarity(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate similarity between query and multiple documents.

        Args:
            query_embedding: Query embedding
            document_embeddings: Document embeddings

        Returns:
            numpy array of similarity scores
        """
        # Normalize if needed
        if self.normalize:
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            document_embeddings = document_embeddings / np.linalg.norm(
                document_embeddings, axis=1, keepdims=True
            )

        return np.dot(document_embeddings, query_embedding)
