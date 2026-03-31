"""Base class for post-ranking filters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from fastrs.core.types import ItemScore


class BaseFilter(ABC):
    """Abstract filter.

    Filters remove or modify items *after* ranking, e.g. to enforce
    business rules, remove already-seen items, etc.
    """

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def apply(self, user_id: str, items: list[ItemScore], context: dict[str, Any] | None = None) -> list[ItemScore]:
        """Return the subset of *items* that pass this filter."""
