from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Type

from fastrs.logging import get_logger
from fastrs.pipeline.base import BasePipeline

logger = get_logger("fastrs.pipeline.registry")


class PipelineRegistry:
    """Thread-safe registry for pipeline instances with hot-swap support."""

    def __init__(self) -> None:
        self._pipelines: Dict[str, BasePipeline] = {}
        self._lock = asyncio.Lock()

    async def add(self, pipeline: BasePipeline) -> None:
        async with self._lock:
            if pipeline.name in self._pipelines:
                await self._pipelines[pipeline.name].shutdown()
            await pipeline.startup()
            self._pipelines[pipeline.name] = pipeline
            logger.info("pipeline_added", name=pipeline.name)

    async def remove(self, name: str) -> bool:
        async with self._lock:
            if name not in self._pipelines:
                return False
            await self._pipelines[name].shutdown()
            del self._pipelines[name]
            logger.info("pipeline_removed", name=name)
            return True

    async def get(self, name: str) -> Optional[BasePipeline]:
        async with self._lock:
            return self._pipelines.get(name)

    async def list(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return [p.get_info() for p in self._pipelines.values()]

    async def hot_swap(self, name: str, new_pipeline: BasePipeline) -> bool:
        """Replace a running pipeline without downtime."""
        async with self._lock:
            if name not in self._pipelines:
                return False
            old = self._pipelines[name]
            await new_pipeline.startup()
            self._pipelines[name] = new_pipeline
            await old.shutdown()
            logger.info("pipeline_hot_swapped", name=name)
            return True

    async def restart(self, name: str) -> bool:
        async with self._lock:
            if name not in self._pipelines:
                return False
            pipeline = self._pipelines[name]
            await pipeline.shutdown()
            await pipeline.startup()
            logger.info("pipeline_restarted", name=name)
            return True

    async def shutdown_all(self) -> None:
        async with self._lock:
            for pipeline in self._pipelines.values():
                await pipeline.shutdown()
            self._pipelines.clear()


_registry: Optional[PipelineRegistry] = None


def get_pipeline_registry() -> PipelineRegistry:
    global _registry
    if _registry is None:
        _registry = PipelineRegistry()
    return _registry
