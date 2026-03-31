from __future__ import annotations

import sys
from typing import Any, Dict

from fastapi import APIRouter

from fastrs import __version__
from fastrs.models.schemas import HealthResponse
from fastrs.pipeline.registry import get_pipeline_registry
from fastrs.recall.registry import get_recall_registry
from fastrs.ranking.registry import get_ranking_registry
from fastrs.filter.registry import get_filter_registry

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse, summary="Basic health check")
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@router.get("/ready", response_model=HealthResponse, summary="Readiness check")
async def readiness() -> HealthResponse:
    details: Dict[str, Any] = {}
    try:
        pipelines = await get_pipeline_registry().list()
        details["pipelines"] = len(pipelines)
        recalls = await get_recall_registry().list()
        details["recall_modules"] = len(recalls)
        rankings = await get_ranking_registry().list()
        details["ranking_modules"] = len(rankings)
        filters = await get_filter_registry().list()
        details["filter_modules"] = len(filters)
        status = "ready"
    except Exception as e:
        status = "not_ready"
        details["error"] = str(e)
    return HealthResponse(status=status, version=__version__, details=details)


@router.get("/live", response_model=HealthResponse, summary="Liveness check")
async def liveness() -> HealthResponse:
    return HealthResponse(
        status="alive",
        version=__version__,
        details={"python": sys.version},
    )
