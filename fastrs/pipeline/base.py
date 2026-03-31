from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BasePipeline(ABC):
    name: str = "base_pipeline"

    @abstractmethod
    async def process(self, data: Any) -> Any:
        """Process the input data and return recommendations."""

    async def startup(self) -> None:
        """Called on pipeline startup."""

    async def shutdown(self) -> None:
        """Called on pipeline shutdown."""

    def get_info(self) -> dict[str, Any]:
        return {"name": self.name, "type": type(self).__name__, "status": "running"}
