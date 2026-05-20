"""
Milvus Vector Store - Milvus implementation for vector storage.
"""

from typing import Dict, List, Optional

from loguru import logger


class MilvusStore:
    """
    Milvus Vector Store for document storage and retrieval.

    Features:
    - Scalable vector storage
    - Metadata filtering
    - Similarity search
    - Collection management
    """

    def __init__(
        self,
        collection_name: str = "ops_knowledge",
        host: str = "localhost",
        port: str = "19530",
        dim: int = 1024,
    ):
        """
        Initialize Milvus store.

        Args:
            collection_name: Name of the collection
            host: Milvus host
            port: Milvus port
            dim: Embedding dimension
        """
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.dim = dim

        # Milvus connection and collection
        self._collection = None
        self._connected = False

    def _connect(self) -> None:
        """Connect to Milvus."""
        if self._connected:
            return

        try:
            from pymilvus import connections

            connections.connect("default", host=self.host, port=self.port)
            self._connected = True

            logger.info(f"Connected to Milvus at {self.host}:{self.port}")

        except ImportError:
            logger.error("pymilvus not installed")
            raise

    def _get_collection(self):
        """Get or create collection."""
        if self._collection is not None:
            return self._collection

        self._connect()

        from pymilvus import Collection, FieldSchema, CollectionSchema, DataType

        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]

        schema = CollectionSchema(fields, description="Ops knowledge base")

        # Get or create collection
        self._collection = Collection(self.collection_name, schema)

        # Create index if not exists
        if not self._collection.has_index():
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024},
            }
            self._collection.create_index("embedding", index_params)

        logger.info(f"Milvus collection '{self.collection_name}' ready")

        return self._collection

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None,
    ) -> None:
        """
        Add documents to the collection.

        Args:
            documents: List of document texts
            embeddings: List of document embeddings
            metadatas: List of document metadata
        """
        import json

        collection = self._get_collection()

        # Prepare data
        data = [
            embeddings,
            documents,
            [json.dumps(m or {}) for m in metadatas],
        ]

        # Insert
        collection.insert(data)

        logger.info(f"Added {len(documents)} documents to Milvus")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        metadata_filter: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query embedding
            top_k: Number of results to return
            metadata_filter: Metadata filters

        Returns:
            List of search results
        """
        import json

        collection = self._get_collection()

        # Build filter expression
        expr = None
        if metadata_filter:
            conditions = []
            for key, value in metadata_filter.items():
                conditions.append(f'metadata["{key}"] == "{value}"')
            expr = " and ".join(conditions)

        # Search parameters
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10},
        }

        # Search
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["content", "metadata"],
        )

        # Format results
        search_results = []
        for hit in results[0]:
            metadata = json.loads(hit.entity.get('metadata', '{}'))
            search_results.append({
                "id": hit.id,
                "content": hit.entity.get('content', ''),
                "metadata": metadata,
                "score": hit.score,
            })

        return search_results

    def delete_documents(self, ids: List[int]) -> None:
        """
        Delete documents by IDs.

        Args:
            ids: List of document IDs to delete
        """
        collection = self._get_collection()

        expr = f"id in {ids}"
        collection.delete(expr)

        logger.info(f"Deleted {len(ids)} documents from Milvus")

    def get_document_count(self) -> int:
        """
        Get number of documents in collection.

        Returns:
            Number of documents
        """
        collection = self._get_collection()
        return collection.num_entities

    def drop_collection(self) -> None:
        """Drop the collection."""
        from pymilvus import utility

        utility.drop_collection(self.collection_name)

        self._collection = None
        logger.info(f"Dropped collection '{self.collection_name}'")

    def flush(self) -> None:
        """Flush collection data to disk."""
        collection = self._get_collection()
        collection.flush()

    def compact(self) -> None:
        """Compact collection data."""
        collection = self._get_collection()
        collection.compact()
