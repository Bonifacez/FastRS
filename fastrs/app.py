"""FastAPI application factory for FastRS."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from fastrs import __version__
from fastrs.api.middleware import RequestLoggingMiddleware
from fastrs.api.routes import health, model, modules, pipeline, recommend
from fastrs.config import FastRSConfig, get_config
from fastrs.core.engine import RecommendationEngine
from fastrs.core.registry import ModuleRegistry
from fastrs.core.types import ModuleType
from fastrs.filter.rules import ExcludeItemsFilter
from fastrs.log import setup_logging
from fastrs.models.manager import ModelManager
from fastrs.ranking.score import PassThroughRanker
from fastrs.recall.popular import PopularityRecall

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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: setup and teardown."""
    config: FastRSConfig = app.state.config
    setup_logging(level=config.log_level, fmt=config.log_format)

    registry = ModuleRegistry()
    _register_defaults(registry)

    app.state.registry = registry
    app.state.engine = RecommendationEngine(registry, config)
    app.state.model_manager = ModelManager(model_dir=config.model_dir)

    yield


def create_app(config: FastRSConfig | None = None) -> FastAPI:
    """Build and return the FastAPI application."""
    config = config or get_config()

    app = FastAPI(
        title="FastRS",
        description="A production-grade Recommendation System for Everything",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.config = config

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
