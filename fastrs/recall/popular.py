"""Built-in recall strategies."""

from __future__ import annotations

import random
from typing import Any

from fastrs.core.types import ItemScore
from fastrs.recall.base import BaseRecall


class PopularityRecall(BaseRecall):
    """Return items ordered by a pre-computed popularity score.

    This is a simple baseline recall: items are sorted by descending
    popularity and the top-K are returned.
    """

    def __init__(self, item_scores: dict[str, float] | None = None) -> None:
        self._item_scores: dict[str, float] = item_scores or {}

    def set_items(self, item_scores: dict[str, float]) -> None:
        """Replace the internal popularity table."""
        self._item_scores = dict(item_scores)

    def recall(self, user_id: str, top_k: int, context: dict[str, Any] | None = None) -> list[ItemScore]:
        sorted_items = sorted(self._item_scores.items(), key=lambda x: x[1], reverse=True)
        return [ItemScore(item_id=iid, score=score) for iid, score in sorted_items[:top_k]]


class RandomRecall(BaseRecall):
    """Return a random sample of items — useful for exploration / testing."""

    def __init__(self, item_ids: list[str] | None = None, seed: int | None = None) -> None:
        self._item_ids: list[str] = item_ids or []
        self._rng = random.Random(seed)

    def set_items(self, item_ids: list[str]) -> None:
        self._item_ids = list(item_ids)

    def recall(self, user_id: str, top_k: int, context: dict[str, Any] | None = None) -> list[ItemScore]:
        k = min(top_k, len(self._item_ids))
        sampled = self._rng.sample(self._item_ids, k)
        return [ItemScore(item_id=iid, score=1.0) for iid in sampled]
