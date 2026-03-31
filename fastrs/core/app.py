from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastrs import __version__
from fastrs.config import get_settings
from fastrs.core.events import lifespan
from fastrs.api.middleware import LatencyMiddleware, RequestIDMiddleware
from fastrs.api.routes import health, recommend, pipeline, model


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="FastRS - Fast Recommendation System",
        description=(
            "High-performance, production-grade recommendation system. "
            "Supports recall, ranking, and filtering modules with hot-swap capability. "
            "Designed to be AI agent friendly with comprehensive REST API."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={"name": "FastRS", "url": "https://github.com/FastRS/FastRS"},
        license_info={"name": "MIT"},
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middlewares (order matters: added last = executed first)
    app.add_middleware(LatencyMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Routers
    app.include_router(health.router)
    app.include_router(recommend.router)
    app.include_router(pipeline.router)
    app.include_router(model.router)

    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "name": "FastRS",
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
        }

    return app
