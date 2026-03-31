from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from fastrs.logging import get_logger
from fastrs.models.schemas import ModuleInfo, PipelineCreateRequest
from fastrs.pipeline.data import DataPipeline
from fastrs.pipeline.registry import get_pipeline_registry
from fastrs.recall.registry import get_recall_registry
from fastrs.ranking.registry import get_ranking_registry
from fastrs.filter.registry import get_filter_registry

router = APIRouter(prefix="/pipelines", tags=["pipelines"])
logger = get_logger("fastrs.routes.pipeline")


@router.get("", response_model=List[Dict[str, Any]], summary="List all pipelines")
async def list_pipelines() -> List[Dict[str, Any]]:
    return await get_pipeline_registry().list()


@router.post("", response_model=Dict[str, Any], summary="Create a new pipeline")
async def create_pipeline(req: PipelineCreateRequest) -> Dict[str, Any]:
    registry = get_pipeline_registry()
    existing = await registry.get(req.name)
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Pipeline '{req.name}' already exists")

    recall_mod = None
    if req.recall_module:
        recall_mod = await get_recall_registry().get(req.recall_module)
        if recall_mod is None:
            raise HTTPException(status_code=404, detail=f"Recall module '{req.recall_module}' not found")

    ranking_mod = None
    if req.ranking_module:
        ranking_mod = await get_ranking_registry().get(req.ranking_module)
        if ranking_mod is None:
            raise HTTPException(status_code=404, detail=f"Ranking module '{req.ranking_module}' not found")

    filter_mods = []
    for fname in (req.filter_modules or []):
        fmod = await get_filter_registry().get(fname)
        if fmod is None:
            raise HTTPException(status_code=404, detail=f"Filter module '{fname}' not found")
        filter_mods.append(fmod)

    pipeline = DataPipeline(
        name=req.name,
        recall_module=recall_mod,
        ranking_module=ranking_mod,
        filter_modules=filter_mods,
        config=req.config,
    )
    await registry.add(pipeline)
    return pipeline.get_info()


@router.delete("/{name}", summary="Remove a pipeline")
async def remove_pipeline(name: str) -> Dict[str, str]:
    removed = await get_pipeline_registry().remove(name)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Pipeline '{name}' not found")
    return {"status": "removed", "name": name}


@router.post("/{name}/restart", summary="Restart a pipeline")
async def restart_pipeline(name: str) -> Dict[str, str]:
    restarted = await get_pipeline_registry().restart(name)
    if not restarted:
        raise HTTPException(status_code=404, detail=f"Pipeline '{name}' not found")
    return {"status": "restarted", "name": name}


@router.get("/{name}", response_model=Dict[str, Any], summary="Get pipeline info")
async def get_pipeline(name: str) -> Dict[str, Any]:
    pipeline = await get_pipeline_registry().get(name)
    if pipeline is None:
        raise HTTPException(status_code=404, detail=f"Pipeline '{name}' not found")
    return pipeline.get_info()
