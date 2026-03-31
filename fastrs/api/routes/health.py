"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from fastrs import __version__

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz() -> dict[str, str]:
    """Readiness probe."""
    return {"status": "ready"}


@router.get("/info")
async def info() -> dict[str, str]:
    """Service information."""
    return {"name": "FastRS", "version": __version__}
