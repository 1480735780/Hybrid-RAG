"""
Vector Retriever - Semantic-based retrieval for Hybrid RAG.
"""

from typing import Dict, List, Optional

import numpy as np
from loguru import logger


class VectorRetriever:
    """
    Vector Retriever for semantic-based document retrieval.

    Features:
    - Multiple vector store support (ChromaDB, Milvus)
    - BGE-M3 embeddings
    - Metadata filtering
    - Similarity search
    """

    def __init__(
        self,
        vector_store_type: str = "chroma",
        embedding_model: Optional[str] = None,
        top_k: int = 20,
    ):
        """
        Initialize vector retriever.

        Args:
            vector_store_type: Type of vector store (chroma, milvus)
            embedding_model: Embedding model name
            top_k: Number of results to return
        """
        self.vector_store_type = vector_store_type
        self.embedding_model = embedding_model
        self.top_k = top_k

        # Components
        self._vector_store = None
        self._embedding_model = None

    def _get_embedding_model(self):
        """Get or create embedding model."""
        if self._embedding_model is not None:
            return self._embedding_model

        from rag.embeddings import EmbeddingModel

        self._embedding_model = EmbeddingModel(
            model_name=self.embedding_model or "BAAI/bge-m3",
        )

        return self._embedding_model

    def _get_vector_store(self):
        """Get or create vector store."""
        if self._vector_store is not None:
            return self._vector_store

        if self.vector_store_type == "chroma":
            self._create_chroma_store()
        elif self.vector_store_type == "milvus":
            self._create_milvus_store()
        else:
            raise ValueError(f"Unsupported vector store type: {self.vector_store_type}")

        return self._vector_store

    def _create_chroma_store(self) -> None:
        """Create ChromaDB vector store."""
        try:
            import chromadb

            # Create persistent client
            client = chromadb.PersistentClient(path="./chroma_db")

            # Get or create collection
            self._vector_store = client.get_or_create_collection(
                name="ops_knowledge",
                metadata={"hnsw:space": "cosine"},
            )

            logger.info("ChromaDB vector store created")

        except ImportError:
            logger.error("chromadb not installed")
            raise

    def _create_milvus_store(self) -> None:
        """Create Milvus vector store."""
        try:
            from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

            # Connect to Milvus
            connections.connect("default", host="localhost", port="19530")

            # Define schema
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ]

            schema = CollectionSchema(fields, description="Ops knowledge base")
            self._vector_store = Collection("ops_knowledge", schema)

            logger.info("Milvus vector store created")

        except ImportError:
            logger.error("pymilvus not installed")
            raise

    def add_documents(
        self,
        documents: List[Dict],
        text_key: str = "content",
    ) -> None:
        """
        Add documents to vector store.

        Args:
            documents: List of documents with content and metadata
            text_key: Key for document text
        """
        vector_store = self._get_vector_store()
        embedding_model = self._get_embedding_model()

        # Extract texts
        texts = [doc.get(text_key, "") for doc in documents]

        # Generate embeddings
        embeddings = embedding_model.encode(texts)

        # Add to vector store
        if self.vector_store_type == "chroma":
            self._add_to_chroma(documents, embeddings, texts)
        elif self.vector_store_type == "milvus":
            self._add_to_milvus(documents, embeddings, texts)

        logger.info(f"Added {len(documents)} documents to vector store")

    def _add_to_chroma(
        self,
        documents: List[Dict],
        embeddings: np.ndarray,
        texts: List[str],
    ) -> None:
        """Add documents to ChromaDB."""
        ids = [str(i) for i in range(len(documents))]
        metadatas = [doc.get("metadata", {}) for doc in documents]

        self._vector_store.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
        )

    def _add_to_milvus(
        self,
        documents: List[Dict],
        embeddings: np.ndarray,
        texts: List[str],
    ) -> None:
        """Add documents to Milvus."""
        import json

        data = [
            embeddings.tolist(),
            texts,
            [json.dumps(doc.get("metadata", {})) for doc in documents],
        ]

        self._vector_store.insert(data)

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Search documents using vector similarity.

        Args:
            query: Search query
            top_k: Number of results to return
            metadata_filter: Metadata filters

        Returns:
            List of search results with scores
        """
        vector_store = self._get_vector_store()
        embedding_model = self._get_embedding_model()

        top_k = top_k or self.top_k

        # Generate query embedding
        query_embedding = embedding_model.encode_query(query)

        # Search in vector store
        if self.vector_store_type == "chroma":
            return self._search_chroma(query_embedding, top_k, metadata_filter)
        elif self.vector_store_type == "milvus":
            return self._search_milvus(query_embedding, top_k, metadata_filter)

        return []

    def _search_chroma(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        metadata_filter: Optional[Dict],
    ) -> List[Dict]:
        """Search in ChromaDB."""
        where = metadata_filter if metadata_filter else None

        results = self._vector_store.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where,
        )

        search_results = []
        for i in range(len(results['ids'][0])):
            search_results.append({
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "score": 1 - results['distances'][0][i],  # Convert distance to similarity
                "id": results['ids'][0][i],
            })

        return search_results

    def _search_milvus(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        metadata_filter: Optional[Dict],
    ) -> List[Dict]:
        """Search in Milvus."""
        import json

        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10},
        }

        # Build filter expression
        expr = None
        if metadata_filter:
            conditions = []
            for key, value in metadata_filter.items():
                conditions.append(f'metadata["{key}"] == "{value}"')
            expr = " and ".join(conditions)

        results = self._vector_store.search(
            data=[query_embedding.tolist()],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["content", "metadata"],
        )

        search_results = []
        for hit in results[0]:
            metadata = json.loads(hit.entity.get('metadata', '{}'))
            search_results.append({
                "content": hit.entity.get('content', ''),
                "metadata": metadata,
                "score": hit.score,
                "id": hit.id,
            })

        return search_results

    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents from vector store.

        Args:
            ids: List of document IDs to delete
        """
        vector_store = self._get_vector_store()

        if self.vector_store_type == "chroma":
            vector_store.delete(ids=ids)
        elif self.vector_store_type == "milvus":
            vector_store.delete(f"id in {ids}")

        logger.info(f"Deleted {len(ids)} documents from vector store")

    def get_document_count(self) -> int:
        """
        Get number of documents in vector store.

        Returns:
            Number of documents
        """
        vector_store = self._get_vector_store()

        if self.vector_store_type == "chroma":
            return vector_store.count()
        elif self.vector_store_type == "milvus":
            return vector_store.num_entities

        return 0
