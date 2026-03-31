"""Base classes for data pipeline stages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BasePipelineStage(ABC):
    """Abstract base for a pipeline stage (load, transform, etc.)."""

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def execute(self, data: Any, **kwargs: Any) -> Any:
        """Run the pipeline stage on *data* and return transformed output."""


class DataLoader(BasePipelineStage):
    """Abstract data loader."""

    @abstractmethod
    def execute(self, data: Any = None, **kwargs: Any) -> list[dict[str, Any]]:
        """Load and return raw item data."""


class DataTransformer(BasePipelineStage):
    """Abstract data transformer."""

    @abstractmethod
    def execute(self, data: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
        """Transform item data in place or return a new list."""
