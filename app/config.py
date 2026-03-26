from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Embedding
    embedding_model: str = "bge-m3"
    embedding_api_url: str = "http://localhost:11434/api"
    embedding_dim: int = 1024

    # Rerank
    rerank_model: str = "bge-reranker-v2-m3"
    rerank_api_url: str = "http://localhost:11434/api"

    # Milvus
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "notes"
    milvus_index_type: str = "hnsw"
    milvus_metric_type: str = "cosine"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl: int = 3600

    # Java API
    java_api_base_url: str = "http://localhost:8080"
    java_api_key: str = ""

    # Server
    agent_host: str = "0.0.0.0"
    agent_port: int = 8000
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
