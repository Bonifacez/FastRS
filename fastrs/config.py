"""Configuration management for FastRS."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class FastRSConfig(BaseSettings):
    """Global configuration loaded from environment variables prefixed with FASTRS_."""

    model_config = {"env_prefix": "FASTRS_"}

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    debug: bool = False

    # Recommendation engine
    default_recall_top_k: int = Field(default=200, description="Default number of candidates to recall")
    default_rank_top_k: int = Field(default=50, description="Default number of items after ranking")
    default_result_top_k: int = Field(default=10, description="Default number of final results returned")

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = ""

    # Model storage
    model_dir: str = "models_store"

    # PostgreSQL (set DSN to enable)
    postgres_dsn: str = ""
    postgres_pool_size: int = Field(default=10, description="PostgreSQL connection pool size")
    postgres_max_overflow: int = Field(default=20, description="Max extra connections beyond pool_size")
    postgres_echo: bool = False

    # Redis (set URL to enable)
    redis_url: str = ""
    redis_max_connections: int = Field(default=20, description="Max Redis pooled connections")

    # Message queue
    mq_backend: str = "auto"
    mq_redis_group: str = "fastrs"
    mq_redis_consumer: str = "worker-0"

    @classmethod
    def settings_customise_sources(
        cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings
    ):
        """Env vars take precedence over init kwargs (YAML values)."""
        return (env_settings, init_settings, file_secret_settings)


def get_config(config_path: str | None = None) -> FastRSConfig:
    """Return a FastRSConfig instance.

    If *config_path* is given, values are loaded from that YAML file (env vars
    still override).
    """
    if config_path:
        from fastrs.config_loader import load_yaml_config, yaml_to_fastrs_config

        yaml_data = load_yaml_config(config_path)
        return yaml_to_fastrs_config(yaml_data)
    return FastRSConfig()
