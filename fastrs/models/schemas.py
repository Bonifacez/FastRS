from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    top_k: int = Field(default=10, ge=1, le=1000, description="Number of items to return")
    filters: Optional[List[str]] = Field(default=None, description="Filter module names to apply")
    pipeline: Optional[str] = Field(default=None, description="Pipeline name to use")

    model_config = {"json_schema_extra": {"example": {
        "user_id": "user_123",
        "context": {"category": "electronics"},
        "top_k": 10,
    }}}


class Item(BaseModel):
    item_id: str = Field(..., description="Item identifier")
    score: float = Field(..., description="Recommendation score")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Item metadata")


class RecommendResponse(BaseModel):
    user_id: str
    items: List[Item]
    pipeline: Optional[str] = None
    latency_ms: Optional[float] = None
    request_id: Optional[str] = None


class BatchRecommendRequest(BaseModel):
    requests: List[RecommendRequest]


class BatchRecommendResponse(BaseModel):
    responses: List[RecommendResponse]
    total_latency_ms: Optional[float] = None


class ModuleInfo(BaseModel):
    name: str
    type: str
    status: str
    config: Optional[Dict[str, Any]] = None


class PipelineCreateRequest(BaseModel):
    name: str = Field(..., description="Pipeline name")
    recall_module: Optional[str] = Field(default=None, description="Recall module name")
    ranking_module: Optional[str] = Field(default=None, description="Ranking module name")
    filter_modules: Optional[List[str]] = Field(default=None, description="Filter module names")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Pipeline config")


class ModelTrainRequest(BaseModel):
    model_name: str
    model_type: str = Field(default="simple_mlp", description="Model architecture type")
    data_path: Optional[str] = None
    epochs: int = Field(default=10, ge=1)
    learning_rate: float = Field(default=0.001, gt=0)
    batch_size: int = Field(default=32, ge=1)
    config: Optional[Dict[str, Any]] = None


class ModelLoadRequest(BaseModel):
    model_name: str
    model_path: str
    model_type: str = Field(default="simple_mlp")


class HealthResponse(BaseModel):
    status: str
    version: str
    details: Optional[Dict[str, Any]] = None
