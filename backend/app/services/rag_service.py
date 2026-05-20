"""
RAG Service - Core RAG pipeline implementation.
Real implementation with BM25, Vector Search, and LLM.
"""

import os
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from loguru import logger

from backend.config.settings import Settings, get_settings


class RAGService:
    """
    RAG Service implementing the complete RAG pipeline.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._initialized = False

        # Components
        self._embedding_model = None
        self._bm25_retriever = None
        self._vector_store = None
        self._reranker = None
        self._llm_client = None

        # Document storage
        self._documents = []
        self._document_chunks = []

    async def initialize(self) -> None:
        """Initialize all RAG components."""
        if self._initialized:
            return

        logger.info("Initializing RAG Service...")

        try:
            # Initialize embedding model
            self._init_embedding_model()

            # Initialize vector store
            self._init_vector_store()

            # Initialize BM25
            self._init_bm25()

            # Initialize LLM
            self._init_llm()

            self._initialized = True
            logger.info("RAG Service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAG Service: {e}")
            raise

    def _init_embedding_model(self):
        """Initialize embedding model."""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.settings.EMBEDDING_MODEL}")
            self._embedding_model = SentenceTransformer(
                self.settings.EMBEDDING_MODEL,
                device=self.settings.EMBEDDING_DEVICE,
            )
            logger.info("Embedding model loaded")

        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}")
            logger.info("Using simple fallback embedding")
            self._embedding_model = None

    def _init_vector_store(self):
        """Initialize vector store."""
        try:
            import chromadb

            # Use persistent client
            persist_dir = os.path.join(os.getcwd(), "chroma_db")
            os.makedirs(persist_dir, exist_ok=True)

            client = chromadb.PersistentClient(path=persist_dir)
            self._vector_store = client.get_or_create_collection(
                name=self.settings.CHROMA_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB vector store initialized")

        except Exception as e:
            logger.warning(f"Failed to init ChromaDB: {e}")
            self._vector_store = None

    def _init_bm25(self):
        """Initialize BM25 retriever."""
        try:
            from rank_bm25 import BM25Okapi
            import jieba

            self._bm25_class = BM25Okapi
            self._jieba = jieba
            self._bm25_corpus = []
            self._bm25_docs = []
            logger.info("BM25 initialized")

        except Exception as e:
            logger.warning(f"Failed to init BM25: {e}")
            self._bm25_class = None

    def _init_llm(self):
        """Initialize LLM client."""
        try:
            if self.settings.LLM_PROVIDER == "openai":
                from openai import AsyncOpenAI

                self._llm_client = AsyncOpenAI(
                    api_key=self.settings.OPENAI_API_KEY,
                    base_url=self.settings.OPENAI_BASE_URL,
                )
                self._llm_model = self.settings.OPENAI_MODEL

            elif self.settings.LLM_PROVIDER == "dashscope":
                from openai import AsyncOpenAI

                self._llm_client = AsyncOpenAI(
                    api_key=self.settings.DASHSCOPE_API_KEY,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                )
                self._llm_model = self.settings.DASHSCOPE_MODEL

            logger.info(f"LLM initialized: {self.settings.LLM_PROVIDER}")

        except Exception as e:
            logger.warning(f"Failed to init LLM: {e}")
            self._llm_client = None

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25."""
        if hasattr(self, '_jieba'):
            return list(self._jieba.cut(text))
        return text.split()

    def add_documents(self, documents: List[Dict]) -> None:
        """Add documents to the index."""
        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            # Store document
            self._documents.append(doc)

            # Tokenize for BM25
            tokens = self._tokenize(content)
            self._bm25_corpus.append(tokens)
            self._bm25_docs.append(doc)

            # Add to vector store
            if self._vector_store is not None and self._embedding_model is not None:
                try:
                    embedding = self._embedding_model.encode(content).tolist()
                    doc_id = str(uuid4())

                    self._vector_store.add(
                        ids=[doc_id],
                        embeddings=[embedding],
                        documents=[content],
                        metadatas=[metadata],
                    )
                except Exception as e:
                    logger.warning(f"Failed to add to vector store: {e}")

        # Rebuild BM25 index
        if self._bm25_class and self._bm25_corpus:
            self._bm25_index = self._bm25_class(self._bm25_corpus)

        logger.info(f"Added {len(documents)} documents to index")

    def _bm25_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Search using BM25."""
        if not hasattr(self, '_bm25_index') or not self._bm25_docs:
            return []

        tokens = self._tokenize(query)
        scores = self._bm25_index.get_scores(tokens)

        # Get top-k indices
        import numpy as np
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "content": self._bm25_docs[idx]["content"],
                    "metadata": self._bm25_docs[idx].get("metadata", {}),
                    "score": float(scores[idx]),
                })

        return results

    def _vector_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Search using vector similarity."""
        if self._vector_store is None or self._embedding_model is None:
            return []

        try:
            query_embedding = self._embedding_model.encode(query).tolist()

            results = self._vector_store.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self._vector_store.count()),
            )

            search_results = []
            for i in range(len(results['ids'][0])):
                search_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "score": 1 - results['distances'][0][i],
                })

            return search_results

        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []

    def _hybrid_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Search using hybrid (BM25 + Vector)."""
        bm25_results = self._bm25_search(query, top_k)
        vector_results = self._vector_search(query, top_k)

        # Normalize scores
        bm25_max = max([r["score"] for r in bm25_results], default=1.0)
        vector_max = max([r["score"] for r in vector_results], default=1.0)

        # Fuse scores
        alpha = self.settings.HYBRID_ALPHA
        fused = {}

        for r in bm25_results:
            key = hash(r["content"])
            fused[key] = {
                **r,
                "score": alpha * (r["score"] / bm25_max),
            }

        for r in vector_results:
            key = hash(r["content"])
            if key in fused:
                fused[key]["score"] += (1 - alpha) * (r["score"] / vector_max)
            else:
                fused[key] = {
                    **r,
                    "score": (1 - alpha) * (r["score"] / vector_max),
                }

        # Sort and return top-k
        results = sorted(fused.values(), key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    async def process_query(
        self,
        query: str,
        history: List[Dict] = None,
        metadata_filter: Optional[Dict] = None,
        use_hybrid: bool = True,
        top_k: int = 5,
    ) -> Dict:
        """Process a query through the RAG pipeline."""
        if not self._initialized:
            await self.initialize()

        logger.info(f"Processing query: {query[:100]}...")

        # Step 1: Retrieve documents
        if use_hybrid:
            retrieved_docs = self._hybrid_search(query, top_k=top_k * 2)
        else:
            retrieved_docs = self._vector_search(query, top_k=top_k * 2)

        # Step 2: Apply metadata filter
        if metadata_filter:
            retrieved_docs = [
                doc for doc in retrieved_docs
                if all(
                    doc.get("metadata", {}).get(k) == v
                    for k, v in metadata_filter.items()
                    if v
                )
            ]

        # Step 3: Take top-k
        context_docs = retrieved_docs[:top_k]

        # Step 4: Generate answer
        answer = await self._generate_answer(query, context_docs, history)

        return {
            "answer": answer,
            "sources": context_docs,
            "query": query,
        }

    async def _generate_answer(
        self,
        query: str,
        context: List[Dict],
        history: Optional[List[Dict]] = None,
    ) -> str:
        """Generate answer using LLM."""
        if self._llm_client is None:
            # Fallback: return context-based answer
            return self._generate_fallback_answer(query, context)

        # Build context string
        context_str = "\n\n".join([
            f"[来源 {i+1}] {doc.get('content', '')}"
            for i, doc in enumerate(context)
        ])

        # Build history string
        history_str = ""
        if history:
            history_str = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in history[-5:]
            ])

        # Build prompt
        system_prompt = """你是一个专业的运维助手，擅长 Linux、Docker、MySQL、Kubernetes、Nginx 等运维技术。
请根据提供的上下文信息回答用户的问题。

要求：
1. 基于上下文给出准确、详细的回答
2. 如果涉及操作步骤，请给出具体的命令
3. 如果上下文信息不足，请说明并给出你的建议
4. 回答要专业、清晰、有条理"""

        user_prompt = f"""请基于以下上下文信息回答问题。

上下文信息：
{context_str}

{f"对话历史：{history_str}" if history_str else ""}

用户问题：{query}

请给出详细的回答："""

        try:
            response = await self._llm_client.chat.completions.create(
                model=self._llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_fallback_answer(query, context)

    def _generate_fallback_answer(self, query: str, context: List[Dict]) -> str:
        """Generate fallback answer without LLM."""
        if not context:
            return f"抱歉，没有找到与 \"{query}\" 相关的知识库内容。请尝试上传相关文档或换个关键词搜索。"

        answer = f"根据知识库检索，找到以下与 \"{query}\" 相关的信息：\n\n"

        for i, doc in enumerate(context[:3], 1):
            content = doc.get("content", "")[:500]
            metadata = doc.get("metadata", {})
            source = metadata.get("filename", "未知来源")

            answer += f"**[{i}] 来源: {source}**\n"
            answer += f"{content}\n\n"

        answer += "---\n"
        answer += "提示：配置 LLM API Key 后可获得更智能的回答。"

        return answer

    def get_document_count(self) -> int:
        """Get number of documents in index."""
        return len(self._documents)

    def clear_index(self) -> None:
        """Clear all documents from index."""
        self._documents = []
        self._bm25_corpus = []
        self._bm25_docs = []

        if self._vector_store:
            try:
                # Delete all from vector store
                all_ids = self._vector_store.get()["ids"]
                if all_ids:
                    self._vector_store.delete(ids=all_ids)
            except:
                pass

        logger.info("Index cleared")
