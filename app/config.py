from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 阿里云百炼 API
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # LLM
    llm_model: str = "qwen3.5-flash"

    # Embedding
    embedding_model: str = "tongyi-embedding-vision-plus-2026-03-06"
    embedding_dim: int = 1536

    # 向量库
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "notes"
    milvus_index_type: str = "hnsw"
    milvus_metric_type: str = "cosine"

    # Redis
    redis_url: str = "redis://localhost:6379/1"
    redis_session_ttl: int = 3600

    # Java 后端
    java_api_base_url: str = "http://localhost:8080"
    java_api_key: str = ""

    # 服务配置
    agent_host: str = "0.0.0.0"
    agent_port: int = 8000
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
