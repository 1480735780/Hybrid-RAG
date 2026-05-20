"""
Application settings and configuration management.
Uses pydantic-settings for environment variable validation.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Enterprise Ops Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # Database (MySQL)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "ops_assistant"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Vector Store
    VECTOR_STORE_TYPE: str = "chroma"  # chroma or milvus
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "ops_knowledge"

    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "ops_knowledge"

    # Embedding Model
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_BATCH_SIZE: int = 32

    # Rerank Model
    RERANK_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RERANK_DEVICE: str = "cpu"
    RERANK_TOP_K: int = 3

    # LLM Configuration
    LLM_PROVIDER: str = "openai"  # openai, dashscope, local

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4-turbo"

    # DashScope (Qwen/DeepSeek)
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_MODEL: str = "qwen-max"

    # Local LLM
    LOCAL_LLM_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    LOCAL_LLM_DEVICE: str = "auto"

    # BM25 Configuration
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    BM25_TOP_K: int = 20

    # Retrieval Configuration
    RETRIEVAL_TOP_K: int = 20
    HYBRID_ALPHA: float = 0.7  # Weight for vector search (0-1)

    # Document Processing
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    MAX_FILE_SIZE_MB: int = 50

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8501"]

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        password = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
