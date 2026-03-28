"""Central configuration — reads from environment / .env"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "Bill Generator"
    version: str = "2.0.0"
    debug: bool = False

    # Paths
    upload_dir: Path = Path("uploads")
    output_dir: Path = Path("outputs")
    template_dir: Path = Path("app/engine/renderer/templates")

    # Limits
    max_upload_mb: int = 20

    # Redis / ARQ
    redis_url: str = "redis://localhost:6379"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure dirs exist
settings.upload_dir.mkdir(exist_ok=True)
settings.output_dir.mkdir(exist_ok=True)
