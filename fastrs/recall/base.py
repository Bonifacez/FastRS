from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from fastrs.models.schemas import Item


class BaseRecall(ABC):
    name: str = "base_recall"

    @abstractmethod
    async def recall(self, query: str, context: Dict[str, Any], top_k: int) -> List[Item]:
        """Recall candidate items for a given query/user."""

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def get_info(self) -> dict[str, Any]:
        return {"name": self.name, "type": type(self).__name__, "status": "running"}
