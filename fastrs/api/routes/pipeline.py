"""Pipeline management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from fastrs.core.types import ModuleInfo, ModuleType

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])


@router.get("/", response_model=list[ModuleInfo])
async def list_pipeline_modules(request: Request) -> list[ModuleInfo]:
    """List registered pipeline modules."""
    registry = getattr(request.app.state, "registry", None)
    if registry is None:
        raise HTTPException(status_code=503, detail="Registry not initialized")
    return registry.list_modules(module_type=ModuleType.PIPELINE)


@router.post("/run")
async def run_pipeline(request: Request, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Trigger a data-pipeline run (placeholder for custom pipeline execution)."""
    registry = getattr(request.app.state, "registry", None)
    if registry is None:
        raise HTTPException(status_code=503, detail="Registry not initialized")
    pipeline_modules = registry.get_instances(ModuleType.PIPELINE, enabled_only=True)
    if not pipeline_modules:
        raise HTTPException(status_code=404, detail="No pipeline modules registered")

    results: dict[str, Any] = {}
    data: Any = None
    for name, stage in pipeline_modules.items():
        data = stage.execute(data, **(config or {}))
        results[name] = {"status": "done", "output_count": len(data) if isinstance(data, list) else 1}
    return {"status": "complete", "stages": results}
