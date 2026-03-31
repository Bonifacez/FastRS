from __future__ import annotations

import time
import uuid
from typing import List

from fastapi import APIRouter, HTTPException, Request

from fastrs.logging import get_logger, RequestLogger
from fastrs.models.schemas import (
    BatchRecommendRequest,
    BatchRecommendResponse,
    RecommendRequest,
    RecommendResponse,
)
from fastrs.pipeline.registry import get_pipeline_registry

router = APIRouter(prefix="/recommend", tags=["recommend"])
request_logger = RequestLogger()
logger = get_logger("fastrs.routes.recommend")


async def _run_recommendation(request: RecommendRequest, req_id: str) -> RecommendResponse:
    registry = get_pipeline_registry()
    pipeline_name = request.pipeline or "default"
    pipeline = await registry.get(pipeline_name)

    if pipeline is None:
        # Try to find any pipeline
        pipelines = await registry.list()
        if pipelines:
            pipeline_name = pipelines[0]["name"]
            pipeline = await registry.get(pipeline_name)

    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail=f"No pipeline available. Requested: '{pipeline_name}'",
        )

    result = await pipeline.process(request)
    result.request_id = req_id
    return result


@router.post(
    "",
    response_model=RecommendResponse,
    summary="Get recommendations for a user",
    description="Run the full recommendation pipeline: recall → rank → filter",
)
async def recommend(request: RecommendRequest, http_request: Request) -> RecommendResponse:
    req_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    start = time.perf_counter()
    try:
        result = await _run_recommendation(request, req_id)
        latency_ms = (time.perf_counter() - start) * 1000
        request_logger.log_recommendation(
            request_id=req_id,
            user_id=request.user_id,
            num_items=len(result.items),
            pipeline=result.pipeline,
            latency_ms=latency_ms,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        request_logger.log_error(req_id, str(e))
        logger.exception("recommendation_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/batch",
    response_model=BatchRecommendResponse,
    summary="Batch recommendations",
    description="Process multiple recommendation requests in parallel",
)
async def batch_recommend(
    batch: BatchRecommendRequest, http_request: Request
) -> BatchRecommendResponse:
    import asyncio

    req_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    start = time.perf_counter()

    async def process_one(req: RecommendRequest) -> RecommendResponse:
        child_id = f"{req_id}-{req.user_id}"
        return await _run_recommendation(req, child_id)

    try:
        responses = await asyncio.gather(
            *[process_one(r) for r in batch.requests],
            return_exceptions=False,
        )
        total_ms = (time.perf_counter() - start) * 1000
        return BatchRecommendResponse(
            responses=list(responses),
            total_latency_ms=round(total_ms, 3),
        )
    except Exception as e:
        logger.exception("batch_recommendation_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
