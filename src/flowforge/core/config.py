from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="FLOWFORGE_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FlowForge ML Serving Platform"
    environment: Literal["local", "test", "staging", "production"] = "local"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    api_host: str = "0.0.0.0"  # noqa: S104 - container bind address is configurable.
    api_port: int = 8000
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://flowforge:flowforge@localhost:5432/flowforge"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    jwt_secret: SecretStr = Field(default=SecretStr("local-only-change-me"))
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    request_timeout_seconds: float = 30.0
    max_request_bytes: int = 10 * 1024 * 1024
    rate_limit_per_minute: int = 120
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
