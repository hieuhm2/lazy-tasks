"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_env: Literal["development", "production"] = "development"
    log_level: str = "INFO"

    # OpenAI
    openai_api_key: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""

    # Database
    postgres_url: str = "postgresql+asyncpg://paea:paea_secret@localhost:5432/paea"

    # Vector DB
    qdrant_url: str = "http://localhost:6333"

    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"

    # Optional: LangSmith
    langchain_tracing_v2: bool = False
    langchain_project: str = "paea"
    langsmith_api_key: str = ""

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def sync_postgres_url(self) -> str:
        """Get synchronous database URL (for Alembic)."""
        return self.postgres_url.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
