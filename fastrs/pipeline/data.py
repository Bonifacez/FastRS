from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from fastrs.logging import get_logger
from fastrs.models.schemas import Item, RecommendRequest, RecommendResponse
from fastrs.pipeline.base import BasePipeline

logger = get_logger("fastrs.pipeline.data")


class DataPipeline(BasePipeline):
    """
    Default data pipeline that chains recall -> rank -> filter.
    Holds references to recall, ranking, and filter modules by name.
    """

    name: str = "default"

    def __init__(
        self,
        name: str = "default",
        recall_module: Any = None,
        ranking_module: Any = None,
        filter_modules: Optional[List[Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.recall_module = recall_module
        self.ranking_module = ranking_module
        self.filter_modules = filter_modules or []
        self.config = config or {}

    async def process(self, data: RecommendRequest) -> RecommendResponse:
        start = time.perf_counter()

        items: List[Item] = []

        # Recall stage
        if self.recall_module is not None:
            recalled = await self.recall_module.recall(
                query=data.user_id,
                context=data.context or {},
                top_k=data.top_k * 5,  # Over-fetch for ranking/filtering
            )
            items = recalled
        else:
            # No recall module: return empty
            items = []

        # Ranking stage
        if self.ranking_module is not None and items:
            items = await self.ranking_module.rank(items, context=data.context or {})

        # Filter stage
        for filt in self.filter_modules:
            if items:
                items = await filt.filter(items)

        # Trim to top_k
        items = items[: data.top_k]

        latency_ms = (time.perf_counter() - start) * 1000
        return RecommendResponse(
            user_id=data.user_id,
            items=items,
            pipeline=self.name,
            latency_ms=round(latency_ms, 3),
        )

    async def startup(self) -> None:
        logger.info("pipeline_startup", name=self.name)

    async def shutdown(self) -> None:
        logger.info("pipeline_shutdown", name=self.name)

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": "DataPipeline",
            "status": "running",
            "config": {
                "recall_module": getattr(self.recall_module, "name", None),
                "ranking_module": getattr(self.ranking_module, "name", None),
                "filter_modules": [getattr(f, "name", None) for f in self.filter_modules],
            },
        }
