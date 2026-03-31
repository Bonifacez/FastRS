from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FASTRS_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of uvicorn workers")
    reload: bool = Field(default=False, description="Enable auto-reload")

    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_json: bool = Field(default=False, description="Enable JSON logging")

    # Redis
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")

    # PyTorch
    enable_torch: bool = Field(default=False, description="Enable PyTorch support")
    model_dir: Path = Field(default=Path("models"), description="Directory for saved models")

    # App
    app_name: str = Field(default="FastRS", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
