"""Core type definitions for FastRS."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ModuleType(str, Enum):
    """Types of pluggable modules in the recommendation pipeline."""

    RECALL = "recall"
    RANKING = "ranking"
    FILTER = "filter"
    PIPELINE = "pipeline"


class ItemScore(BaseModel):
    """An item with its recommendation score."""

    item_id: str
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecommendRequest(BaseModel):
    """Request payload for recommendations."""

    user_id: str
    context: dict[str, Any] = Field(default_factory=dict)
    top_k: int = Field(default=10, ge=1, le=1000)
    recall_top_k: int | None = None
    rank_top_k: int | None = None
    recall_strategies: list[str] | None = None
    ranking_strategy: str | None = None
    filter_strategies: list[str] | None = None


class RecommendResponse(BaseModel):
    """Response payload for recommendations."""

    user_id: str
    items: list[ItemScore]
    meta: dict[str, Any] = Field(default_factory=dict)


class ModuleInfo(BaseModel):
    """Information about a registered module."""

    name: str
    module_type: ModuleType
    enabled: bool = True
    description: str = ""


class ModelInfo(BaseModel):
    """Information about a managed model."""

    name: str
    version: str = "0.0.1"
    status: str = "idle"
    path: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
