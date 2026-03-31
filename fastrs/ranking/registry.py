from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastrs.logging import get_logger
from fastrs.ranking.base import BaseRanking

logger = get_logger("fastrs.ranking.registry")


class RankingRegistry:
    def __init__(self) -> None:
        self._modules: Dict[str, BaseRanking] = {}
        self._lock = asyncio.Lock()

    async def add(self, module: BaseRanking) -> None:
        async with self._lock:
            await module.startup()
            self._modules[module.name] = module
            logger.info("ranking_module_added", name=module.name)

    async def remove(self, name: str) -> bool:
        async with self._lock:
            if name not in self._modules:
                return False
            await self._modules[name].shutdown()
            del self._modules[name]
            return True

    async def get(self, name: str) -> Optional[BaseRanking]:
        async with self._lock:
            return self._modules.get(name)

    async def list(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return [m.get_info() for m in self._modules.values()]


_registry: Optional[RankingRegistry] = None


def get_ranking_registry() -> RankingRegistry:
    global _registry
    if _registry is None:
        _registry = RankingRegistry()
    return _registry
