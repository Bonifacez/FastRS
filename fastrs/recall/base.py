"""Base class for recall (candidate generation) strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from fastrs.core.types import ItemScore


class BaseRecall(ABC):
    """Abstract recall strategy.

    A recall strategy generates a broad set of candidate items
    given a user id and optional context.
    """

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def recall(self, user_id: str, top_k: int, context: dict[str, Any] | None = None) -> list[ItemScore]:
        """Return up to *top_k* candidate items for the given user."""
