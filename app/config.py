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
    max_context_tokens: int = 4000

    # Embedding
    embedding_model: str = "text-embedding-v4"
    embedding_dim: int = 1536

    # 向量库
    milvus_mode: str = "remote"  # "lite" 使用本地文件, "remote" 远程连接
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "notes"
    milvus_index_type: str = "hnsw"
    milvus_metric_type: str = "cosine"
    milvus_uri: str = "./data/milvus.db"  # Lite 模式下的本地文件路径

    # Redis
    redis_url: str = "redis://localhost:6379/1"
    redis_session_ttl: int = 3600
    redis_max_history: int = 20
    # Java 后端
    java_api_base_url: str = "http://localhost:8080"
    java_api_key: str = ""

    # 服务配置
    agent_host: str = "0.0.0.0"
    agent_port: int = 8000
    log_level: str = "INFO"

    # RabbitMQ 配置
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 15672
    rabbitmq_username: str = "admin"
    rabbitmq_password: str = "admin123"
    rabbitmq_queue: str = "note.vector.sync.queue"
    rabbitmq_exchange: str = "note.exchange"
    rabbitmq_routing_key: str = "note.vector.sync"


@lru_cache
def get_settings() -> Settings:
    return Settings()
