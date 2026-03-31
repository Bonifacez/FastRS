"""Base class for ranking (scoring) strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from fastrs.core.types import ItemScore


class BaseRanker(ABC):
    """Abstract ranker.

    A ranker takes candidate items from the recall stage and
    re-scores / re-orders them.
    """

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def rank(self, user_id: str, candidates: list[ItemScore], context: dict[str, Any] | None = None) -> list[ItemScore]:
        """Re-score and sort *candidates* for the given user."""
