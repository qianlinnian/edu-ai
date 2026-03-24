from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "EduAI Platform"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://eduai:eduai123@localhost:5432/eduai"
    DATABASE_SYNC_URL: str = "postgresql://eduai:eduai123@localhost:5432/eduai"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "eduai"

    # LLM - 通义千问
    DASHSCOPE_API_KEY: str = ""
    QWEN_MODEL: str = "qwen-max"
    QWEN_VL_MODEL: str = "qwen-vl-max"
    QWEN_EMBEDDING_MODEL: str = "text-embedding-v3"

    # LLM - 智谱
    ZHIPU_API_KEY: str = ""
    ZHIPU_MODEL: str = "glm-4"

    # LLM 默认提供者
    DEFAULT_LLM_PROVIDER: str = "dashscope"  # dashscope | zhipu

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
