"""Health check endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from fastrs import __version__

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request) -> dict[str, Any]:
    """Readiness probe — includes optional PostgreSQL / Redis status."""
    result: dict[str, Any] = {"status": "ready"}

    pg = getattr(request.app.state, "postgres", None)
    if pg is not None:
        result["postgres"] = "ok" if await pg.ping() else "unavailable"

    redis_mgr = getattr(request.app.state, "redis", None)
    if redis_mgr is not None:
        result["redis"] = "ok" if await redis_mgr.ping() else "unavailable"

    return result


@router.get("/info")
async def info() -> dict[str, str]:
    """Service information."""
    return {"name": "FastRS", "version": __version__}
