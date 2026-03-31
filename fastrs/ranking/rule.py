from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from fastrs.logging import get_logger
from fastrs.models.schemas import Item
from fastrs.ranking.base import BaseRanking

logger = get_logger("fastrs.ranking.rule")


class RuleBasedRanking(BaseRanking):
    """
    Rule-based ranking that combines multiple scoring signals:
    - Base score from recall
    - Popularity boost
    - Freshness decay
    - Custom boosts from context
    """

    name: str = "rule_ranking"

    def __init__(
        self,
        name: str = "rule_ranking",
        popularity_weight: float = 0.3,
        freshness_weight: float = 0.2,
        score_weight: float = 0.5,
        freshness_decay_days: float = 30.0,
    ) -> None:
        self.name = name
        self.popularity_weight = popularity_weight
        self.freshness_weight = freshness_weight
        self.score_weight = score_weight
        self.freshness_decay_days = freshness_decay_days
        self._popularity: Dict[str, float] = {}

    def set_popularity(self, item_id: str, popularity: float) -> None:
        self._popularity[item_id] = popularity

    def _compute_score(self, item: Item, context: Dict[str, Any]) -> float:
        base_score = item.score * self.score_weight

        # Popularity
        pop = self._popularity.get(item.item_id, 0.5)
        pop_score = pop * self.popularity_weight

        # Freshness from metadata
        freshness = 1.0
        if item.metadata and "timestamp" in item.metadata:
            age_hours = (time.time() - item.metadata["timestamp"]) / 3600
            freshness = max(0.0, 1.0 - age_hours / (24 * self.freshness_decay_days))
        fresh_score = freshness * self.freshness_weight

        # Context boosts
        boost = 1.0
        if item.metadata and context.get("category"):
            if item.metadata.get("category") == context["category"]:
                boost = 1.5

        return (base_score + pop_score + fresh_score) * boost

    async def rank(self, items: List[Item], context: Dict[str, Any]) -> List[Item]:
        scored = [(item, self._compute_score(item, context)) for item in items]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            Item(item_id=item.item_id, score=score, metadata=item.metadata)
            for item, score in scored
        ]
