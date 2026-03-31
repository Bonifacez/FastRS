"""Recommendation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from fastrs.core.types import RecommendRequest, RecommendResponse

router = APIRouter(prefix="/api/v1", tags=["recommend"])


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(request: Request, body: RecommendRequest) -> RecommendResponse:
    """Generate recommendations for a user."""
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="Recommendation engine not initialized")
    try:
        return engine.recommend(body)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
