"""FastAPI application factory for FastRS."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from fastrs import __version__
from fastrs.api.middleware import RequestLoggingMiddleware
from fastrs.api.routes import health, model, modules, pipeline, recommend
from fastrs.config import FastRSConfig, get_config
from fastrs.core.engine import RecommendationEngine
from fastrs.core.registry import ModuleRegistry
from fastrs.core.types import ModuleType
from fastrs.db.postgres import PostgresManager
from fastrs.db.redis import RedisManager
from fastrs.filter.rules import ExcludeItemsFilter
from fastrs.log import get_logger, setup_logging
from fastrs.models.manager import ModelManager
from fastrs.mq.memory import InMemoryMessageQueue
from fastrs.ranking.score import PassThroughRanker
from fastrs.recall.popular import PopularityRecall

logger = get_logger(__name__)

# -- dependency helpers (access via request.app.state) -------------------------


def get_registry(request: Request) -> ModuleRegistry:
    """Retrieve the module registry from app state."""
    return request.app.state.registry


def get_engine(request: Request) -> RecommendationEngine:
    """Retrieve the recommendation engine from app state."""
    return request.app.state.engine


def get_model_manager(request: Request) -> ModelManager:
    """Retrieve the model manager from app state."""
    return request.app.state.model_manager


def _register_defaults(registry: ModuleRegistry) -> None:
    """Register built-in demo modules so the system works out of the box."""
    registry.register("popularity", ModuleType.RECALL, PopularityRecall(), description="Popularity-based recall")
    registry.register("passthrough", ModuleType.RANKING, PassThroughRanker(), description="Pass-through ranker")
    registry.register("exclude_items", ModuleType.FILTER, ExcludeItemsFilter(), description="Exclude items filter")


def _register_modules_from_config(registry: ModuleRegistry, modules_config: dict[str, Any]) -> None:
    """Instantiate and register modules from YAML config."""
    from fastrs.config_loader import ModuleDefinition, resolve_class

    type_mapping = {
        "recall": ModuleType.RECALL,
        "ranking": ModuleType.RANKING,
        "filter": ModuleType.FILTER,
    }
    for section_name, module_type in type_mapping.items():
        for entry in modules_config.get(section_name, []):
            defn = ModuleDefinition.model_validate(entry)
            cls = resolve_class(defn.class_ref)
            instance = cls(**defn.params)
            registry.register(defn.name, module_type, instance, description=defn.description)
            if not defn.enabled:
                registry.disable(defn.name)


def _register_pipeline_from_config(registry: ModuleRegistry, pipeline_config: list[dict[str, Any]]) -> None:
    """Instantiate and register pipeline stages from YAML config."""
    from fastrs.config_loader import PipelineStageDefinition, resolve_class

    for entry in pipeline_config:
        defn = PipelineStageDefinition.model_validate(entry)
        cls = resolve_class(defn.class_ref)
        instance = cls(**defn.params)
        registry.register(defn.name, ModuleType.PIPELINE, instance, description=defn.description)


def _load_models_from_config(model_manager: ModelManager, models_config: list[dict[str, Any]]) -> None:
    """Instantiate and register models from YAML config."""
    from fastrs.config_loader import ModelDefinition, resolve_class

    for entry in models_config:
        defn = ModelDefinition.model_validate(entry)
        cls = resolve_class(defn.class_ref)
        model_instance = cls(**defn.params)
        model_manager.register(defn.name, model_instance, version=defn.version)
        if defn.path:
            model_manager.load_model(defn.name, defn.path)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: setup and teardown."""
    config: FastRSConfig = app.state.config
    yaml_data: dict[str, Any] = getattr(app.state, "yaml_data", {})

    setup_logging(level=config.log_level, fmt=config.log_format, log_file=config.log_file)

    # -- core ------------------------------------------------------------------
    registry = ModuleRegistry()

    # Register modules from YAML config or fall back to built-in defaults.
    if "modules" in yaml_data:
        _register_modules_from_config(registry, yaml_data["modules"])
    else:
        _register_defaults(registry)

    # Register pipeline stages from YAML config.
    if "pipeline" in yaml_data and yaml_data["pipeline"]:
        _register_pipeline_from_config(registry, yaml_data["pipeline"])

    app.state.registry = registry
    app.state.engine = RecommendationEngine(registry, config)
    app.state.model_manager = ModelManager(model_dir=config.model_dir)

    # Load models from YAML config.
    if "models" in yaml_data and yaml_data["models"]:
        _load_models_from_config(app.state.model_manager, yaml_data["models"])

    # -- PostgreSQL (optional) -------------------------------------------------
    pg = PostgresManager()
    if config.postgres_dsn:
        await pg.connect(
            config.postgres_dsn,
            pool_size=config.postgres_pool_size,
            max_overflow=config.postgres_max_overflow,
            echo=config.postgres_echo,
        )
    app.state.postgres = pg

    # -- Redis (optional) ------------------------------------------------------
    redis_mgr = RedisManager()
    if config.redis_url:
        await redis_mgr.connect(config.redis_url, max_connections=config.redis_max_connections)
    app.state.redis = redis_mgr

    # -- Message Queue ---------------------------------------------------------
    use_redis_mq = config.mq_backend == "redis" or (config.mq_backend == "auto" and config.redis_url)
    if use_redis_mq:
        from fastrs.mq.redis_stream import RedisStreamMessageQueue

        mq = RedisStreamMessageQueue(redis_mgr.client)
        logger.info("mq_backend", backend="redis_stream")
    else:
        mq = InMemoryMessageQueue()
        logger.info("mq_backend", backend="in_memory")
    app.state.mq = mq

    yield

    # -- teardown --------------------------------------------------------------
    await mq.close()
    await redis_mgr.disconnect()
    await pg.disconnect()


def create_app(config: FastRSConfig | None = None) -> FastAPI:
    """Build and return the FastAPI application."""
    config_path = os.environ.get("FASTRS_CONFIG_FILE")

    if config is None:
        config = get_config(config_path)

    # Load raw YAML data for module/pipeline/model definitions.
    yaml_data: dict[str, Any] = {}
    if config_path:
        from fastrs.config_loader import load_yaml_config

        yaml_data = load_yaml_config(config_path)

    app = FastAPI(
        title="FastRS",
        description="A production-grade Recommendation System for Everything",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.config = config
    app.state.yaml_data = yaml_data

    # -- middleware ------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    # -- routes ----------------------------------------------------------------
    app.include_router(health.router)
    app.include_router(recommend.router)
    app.include_router(modules.router)
    app.include_router(pipeline.router)
    app.include_router(model.router)

    return app
