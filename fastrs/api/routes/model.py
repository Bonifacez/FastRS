"""Model management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from fastrs.core.types import ModelInfo

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("/", response_model=list[ModelInfo])
async def list_models(request: Request) -> list[ModelInfo]:
    """List all managed models."""
    manager = getattr(request.app.state, "model_manager", None)
    if manager is None:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    return manager.list_models()


@router.get("/{name}", response_model=ModelInfo)
async def get_model_info(request: Request, name: str) -> ModelInfo:
    """Get info about a specific model."""
    manager = getattr(request.app.state, "model_manager", None)
    if manager is None:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    try:
        return manager.get_info(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not found")


@router.post("/{name}/save")
async def save_model(request: Request, name: str) -> dict[str, str]:
    """Save model weights to disk."""
    manager = getattr(request.app.state, "model_manager", None)
    if manager is None:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    try:
        path = manager.save_model(name)
    except (KeyError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "saved", "path": path}


@router.delete("/{name}")
async def unregister_model(request: Request, name: str) -> dict[str, str]:
    """Remove a model from management."""
    manager = getattr(request.app.state, "model_manager", None)
    if manager is None:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    try:
        manager.unregister(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not found")
    return {"status": "unregistered", "name": name}
