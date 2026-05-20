"""
ChromaDB Vector Store - ChromaDB implementation for vector storage.
"""

from typing import Dict, List, Optional

from loguru import logger


class ChromaStore:
    """
    ChromaDB Vector Store for document storage and retrieval.

    Features:
    - Persistent storage
    - Metadata filtering
    - Similarity search
    - Collection management
    """

    def __init__(
        self,
        collection_name: str = "ops_knowledge",
        persist_directory: str = "./chroma_db",
    ):
        """
        Initialize ChromaDB store.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory for persistent storage
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # ChromaDB client and collection
        self._client = None
        self._collection = None

    def _get_client(self):
        """Get or create ChromaDB client."""
        if self._client is not None:
            return self._client

        try:
            import chromadb

            self._client = chromadb.PersistentClient(path=self.persist_directory)
            logger.info(f"ChromaDB client initialized at {self.persist_directory}")

            return self._client

        except ImportError:
            logger.error("chromadb not installed")
            raise

    def _get_collection(self):
        """Get or create collection."""
        if self._collection is not None:
            return self._collection

        client = self._get_client()

        self._collection = client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(f"ChromaDB collection '{self.collection_name}' ready")

        return self._collection

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """
        Add documents to the collection.

        Args:
            documents: List of document texts
            embeddings: List of document embeddings
            metadatas: List of document metadata
            ids: List of document IDs
        """
        collection = self._get_collection()

        # Generate IDs if not provided
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]

        # Add documents
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(f"Added {len(documents)} documents to ChromaDB")

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
        collection = self._get_collection()

        # Build where clause
        where = metadata_filter if metadata_filter else None

        # Query
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )

        # Format results
        search_results = []
        for i in range(len(results['ids'][0])):
            search_results.append({
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "score": 1 - results['distances'][0][i],  # Convert distance to similarity
            })

        return search_results

    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents by IDs.

        Args:
            ids: List of document IDs to delete
        """
        collection = self._get_collection()
        collection.delete(ids=ids)

        logger.info(f"Deleted {len(ids)} documents from ChromaDB")

    def update_documents(
        self,
        ids: List[str],
        documents: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[Dict]] = None,
    ) -> None:
        """
        Update documents.

        Args:
            ids: List of document IDs to update
            documents: Updated document texts
            embeddings: Updated embeddings
            metadatas: Updated metadata
        """
        collection = self._get_collection()

        collection.update(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(f"Updated {len(ids)} documents in ChromaDB")

    def get_document_count(self) -> int:
        """
        Get number of documents in collection.

        Returns:
            Number of documents
        """
        collection = self._get_collection()
        return collection.count()

    def get_document(self, id: str) -> Optional[Dict]:
        """
        Get document by ID.

        Args:
            id: Document ID

        Returns:
            Document or None
        """
        collection = self._get_collection()

        results = collection.get(ids=[id])

        if results['ids']:
            return {
                "id": results['ids'][0],
                "content": results['documents'][0],
                "metadata": results['metadatas'][0],
            }

        return None

    def list_collections(self) -> List[str]:
        """
        List all collections.

        Returns:
            List of collection names
        """
        client = self._get_client()
        return [col.name for col in client.list_collections()]

    def delete_collection(self) -> None:
        """Delete the collection."""
        client = self._get_client()
        client.delete_collection(self.collection_name)

        self._collection = None
        logger.info(f"Deleted collection '{self.collection_name}'")
