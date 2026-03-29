"""
Centralised application settings — loaded once at startup.
All env vars, paths, and tunable defaults live here.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Security
    secret_key: str = ""
    allow_insecure_secret: bool = False

    # CORS — comma-separated list of allowed origins
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Upload limits
    upload_limit_mb: int = 20

    # Worker
    worker_concurrency: int = 4

    # Template version used by the generation pipeline
    default_template_version: str = "v2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def upload_limit_bytes(self) -> int:
        return self.upload_limit_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
