"""Built-in ranking strategies."""

from __future__ import annotations

from typing import Any

from fastrs.core.types import ItemScore
from fastrs.ranking.base import BaseRanker


class PassThroughRanker(BaseRanker):
    """Return candidates as-is (no re-scoring). Useful as a default / baseline."""

    def rank(self, user_id: str, candidates: list[ItemScore], context: dict[str, Any] | None = None) -> list[ItemScore]:
        return sorted(candidates, key=lambda x: x.score, reverse=True)


class WeightedFieldRanker(BaseRanker):
    """Score items by weighted sum of numeric metadata fields.

    Example: ``WeightedFieldRanker({"rating": 0.7, "popularity": 0.3})``
    """

    def __init__(self, weights: dict[str, float]) -> None:
        self.weights = weights

    def rank(self, user_id: str, candidates: list[ItemScore], context: dict[str, Any] | None = None) -> list[ItemScore]:
        scored: list[ItemScore] = []
        for item in candidates:
            total = sum(
                float(item.metadata.get(field, 0.0)) * weight for field, weight in self.weights.items()
            )
            scored.append(item.model_copy(update={"score": total}))
        return sorted(scored, key=lambda x: x.score, reverse=True)
