"""Built-in filter rules."""

from __future__ import annotations

from typing import Any

from fastrs.core.types import ItemScore
from fastrs.filter.base import BaseFilter


class ExcludeItemsFilter(BaseFilter):
    """Remove specific item IDs (e.g. already purchased / seen)."""

    def __init__(self, excluded_ids: set[str] | None = None) -> None:
        self._excluded: set[str] = excluded_ids or set()

    def set_excluded(self, ids: set[str]) -> None:
        self._excluded = set(ids)

    def apply(self, user_id: str, items: list[ItemScore], context: dict[str, Any] | None = None) -> list[ItemScore]:
        excluded = self._excluded | set(context.get("exclude_ids", [])) if context else self._excluded
        return [item for item in items if item.item_id not in excluded]


class MinScoreFilter(BaseFilter):
    """Remove items whose score is below a threshold."""

    def __init__(self, min_score: float = 0.0) -> None:
        self.min_score = min_score

    def apply(self, user_id: str, items: list[ItemScore], context: dict[str, Any] | None = None) -> list[ItemScore]:
        return [item for item in items if item.score >= self.min_score]
