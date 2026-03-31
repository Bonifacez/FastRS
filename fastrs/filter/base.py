from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List

from fastrs.models.schemas import Item


class BaseFilter(ABC):
    name: str = "base_filter"

    @abstractmethod
    async def filter(self, items: List[Item]) -> List[Item]:
        """Filter and return the filtered list of items."""

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def get_info(self) -> dict[str, Any]:
        return {"name": self.name, "type": type(self).__name__, "status": "running"}
