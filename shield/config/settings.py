from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SCD-SHIELD"
    app_version: str = "0.1.0"

    environment: str = "development"

    llm_provider: str = "fake"
    openai_api_key: str | None = Field(default=None)
    openai_model: str = "gpt-4o-mini"

    max_repair_attempts: int = 2
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
