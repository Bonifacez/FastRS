"""Recommendation engine — orchestrates recall → ranking → filter pipeline."""

from __future__ import annotations

from typing import Any

from fastrs.config import FastRSConfig
from fastrs.core.registry import ModuleRegistry
from fastrs.core.types import ItemScore, ModuleType, RecommendRequest, RecommendResponse
from fastrs.log import get_logger

logger = get_logger(__name__)


class RecommendationEngine:
    """Central engine that drives the recommendation pipeline.

    It reads recall / ranking / filter modules from the shared
    :class:`ModuleRegistry` so that callers can hot-plug new strategies
    at runtime.
    """

    def __init__(self, registry: ModuleRegistry, config: FastRSConfig) -> None:
        self.registry = registry
        self.config = config

    def recommend(self, request: RecommendRequest) -> RecommendResponse:
        """Run the full recommendation pipeline for a single request."""
        recall_top_k = request.recall_top_k or self.config.default_recall_top_k
        rank_top_k = request.rank_top_k or self.config.default_rank_top_k
        result_top_k = request.top_k

        # -- 1. Recall ----------------------------------------------------------
        candidates = self._run_recall(request.user_id, recall_top_k, request.context, request.recall_strategies)

        # -- 2. Ranking ---------------------------------------------------------
        ranked = self._run_ranking(request.user_id, candidates, request.context, request.ranking_strategy)
        ranked = ranked[:rank_top_k]

        # -- 3. Filtering -------------------------------------------------------
        filtered = self._run_filters(request.user_id, ranked, request.context, request.filter_strategies)

        final = filtered[:result_top_k]
        logger.info(
            "recommendation_complete",
            user_id=request.user_id,
            recalled=len(candidates),
            ranked=len(ranked),
            filtered=len(filtered),
            returned=len(final),
        )
        return RecommendResponse(user_id=request.user_id, items=final)

    # -- internal helpers -------------------------------------------------------

    def _run_recall(
        self, user_id: str, top_k: int, context: dict[str, Any], strategy_names: list[str] | None
    ) -> list[ItemScore]:
        recall_modules = self.registry.get_instances(ModuleType.RECALL, enabled_only=True)
        if strategy_names:
            recall_modules = {k: v for k, v in recall_modules.items() if k in strategy_names}
        if not recall_modules:
            logger.warning("no_recall_modules", user_id=user_id)
            return []
        merged: dict[str, ItemScore] = {}
        for _name, module in recall_modules.items():
            for item in module.recall(user_id, top_k, context):
                if item.item_id not in merged or item.score > merged[item.item_id].score:
                    merged[item.item_id] = item
        return sorted(merged.values(), key=lambda x: x.score, reverse=True)

    def _run_ranking(
        self, user_id: str, candidates: list[ItemScore], context: dict[str, Any], strategy_name: str | None
    ) -> list[ItemScore]:
        ranking_modules = self.registry.get_instances(ModuleType.RANKING, enabled_only=True)
        if strategy_name and strategy_name in ranking_modules:
            return ranking_modules[strategy_name].rank(user_id, candidates, context)
        if ranking_modules:
            first = next(iter(ranking_modules.values()))
            return first.rank(user_id, candidates, context)
        return sorted(candidates, key=lambda x: x.score, reverse=True)

    def _run_filters(
        self, user_id: str, items: list[ItemScore], context: dict[str, Any], filter_names: list[str] | None
    ) -> list[ItemScore]:
        filter_modules = self.registry.get_instances(ModuleType.FILTER, enabled_only=True)
        if filter_names:
            filter_modules = {k: v for k, v in filter_modules.items() if k in filter_names}
        for _name, module in filter_modules.items():
            items = module.apply(user_id, items, context)
        return items
