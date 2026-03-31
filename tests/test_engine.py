"""Tests for the recommendation engine."""

from fastrs.config import FastRSConfig
from fastrs.core.engine import RecommendationEngine
from fastrs.core.registry import ModuleRegistry
from fastrs.core.types import ModuleType, RecommendRequest
from fastrs.filter.rules import ExcludeItemsFilter
from fastrs.ranking.score import PassThroughRanker
from fastrs.recall.popular import PopularityRecall


def _build_engine() -> RecommendationEngine:
    registry = ModuleRegistry()
    config = FastRSConfig(default_recall_top_k=100, default_rank_top_k=50, default_result_top_k=5)

    recall = PopularityRecall({"i1": 10, "i2": 8, "i3": 6, "i4": 4, "i5": 2, "i6": 1})
    registry.register("pop", ModuleType.RECALL, recall)
    registry.register("ranker", ModuleType.RANKING, PassThroughRanker())
    registry.register("exclude", ModuleType.FILTER, ExcludeItemsFilter())

    return RecommendationEngine(registry, config)


def test_full_pipeline() -> None:
    engine = _build_engine()
    resp = engine.recommend(RecommendRequest(user_id="u1", top_k=3))
    assert resp.user_id == "u1"
    assert len(resp.items) == 3
    assert resp.items[0].item_id == "i1"


def test_pipeline_with_exclude() -> None:
    engine = _build_engine()
    resp = engine.recommend(
        RecommendRequest(user_id="u1", top_k=3, context={"exclude_ids": ["i1", "i2"]})
    )
    assert all(i.item_id not in ("i1", "i2") for i in resp.items)
    assert resp.items[0].item_id == "i3"


def test_pipeline_no_modules() -> None:
    registry = ModuleRegistry()
    config = FastRSConfig()
    engine = RecommendationEngine(registry, config)
    resp = engine.recommend(RecommendRequest(user_id="u1"))
    assert resp.items == []
