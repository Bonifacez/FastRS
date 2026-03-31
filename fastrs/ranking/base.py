from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from fastrs.models.schemas import Item


class BaseRanking(ABC):
    name: str = "base_ranking"

    @abstractmethod
    async def rank(self, items: List[Item], context: Dict[str, Any]) -> List[Item]:
        """Rank items and return sorted list."""

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def get_info(self) -> dict[str, Any]:
        return {"name": self.name, "type": type(self).__name__, "status": "running"}
