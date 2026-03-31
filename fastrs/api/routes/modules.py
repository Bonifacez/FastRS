"""Module management endpoints (hot-plug support)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from fastrs.core.types import ModuleInfo, ModuleType

router = APIRouter(prefix="/api/v1/modules", tags=["modules"])


@router.get("/", response_model=list[ModuleInfo])
async def list_modules(
    request: Request, module_type: ModuleType | None = None, enabled_only: bool = False
) -> list[ModuleInfo]:
    """List registered modules."""
    registry = getattr(request.app.state, "registry", None)
    if registry is None:
        raise HTTPException(status_code=503, detail="Registry not initialized")
    return registry.list_modules(module_type=module_type, enabled_only=enabled_only)


@router.post("/{name}/enable")
async def enable_module(request: Request, name: str) -> dict[str, str]:
    """Enable a module at runtime."""
    registry = getattr(request.app.state, "registry", None)
    if registry is None:
        raise HTTPException(status_code=503, detail="Registry not initialized")
    try:
        registry.enable(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
    return {"status": "enabled", "name": name}


@router.post("/{name}/disable")
async def disable_module(request: Request, name: str) -> dict[str, str]:
    """Disable a module at runtime."""
    registry = getattr(request.app.state, "registry", None)
    if registry is None:
        raise HTTPException(status_code=503, detail="Registry not initialized")
    try:
        registry.disable(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
    return {"status": "disabled", "name": name}


@router.delete("/{name}")
async def unregister_module(request: Request, name: str) -> dict[str, str]:
    """Unregister a module at runtime."""
    registry = getattr(request.app.state, "registry", None)
    if registry is None:
        raise HTTPException(status_code=503, detail="Registry not initialized")
    try:
        registry.unregister(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
    return {"status": "unregistered", "name": name}
