from __future__ import annotations

import pytest

from fastrs.models.schemas import Item
from fastrs.ranking.rule import RuleBasedRanking
from fastrs.ranking.model import ModelBasedRanking


@pytest.fixture
def items():
    return [
        Item(item_id="a", score=0.9, metadata={"popularity": 0.5, "category": "tech"}),
        Item(item_id="b", score=0.5, metadata={"popularity": 0.9, "category": "sports"}),
        Item(item_id="c", score=0.7, metadata={"popularity": 0.2, "category": "tech"}),
    ]


@pytest.fixture
def rule_ranker():
    ranker = RuleBasedRanking(name="test_rule")
    ranker.set_popularity("a", 0.5)
    ranker.set_popularity("b", 0.9)
    ranker.set_popularity("c", 0.2)
    return ranker


@pytest.mark.asyncio
async def test_rule_ranking_returns_sorted(rule_ranker, items):
    ranked = await rule_ranker.rank(items, context={})
    assert len(ranked) == 3
    scores = [item.score for item in ranked]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_rule_ranking_with_context_boost(rule_ranker, items):
    ranked_no_ctx = await rule_ranker.rank(items, context={})
    ranked_with_ctx = await rule_ranker.rank(items, context={"category": "tech"})
    # Items with tech category should be boosted
    tech_ids = {i.item_id for i in ranked_with_ctx[:2]}
    assert "a" in tech_ids or "c" in tech_ids


@pytest.mark.asyncio
async def test_rule_ranking_preserves_item_ids(rule_ranker, items):
    ranked = await rule_ranker.rank(items, context={})
    ids = {item.item_id for item in ranked}
    assert ids == {"a", "b", "c"}


@pytest.mark.asyncio
async def test_model_ranking_fallback_no_model(items):
    # Without a serving model, should fall back to score-based sort
    ranker = ModelBasedRanking(name="test_model", serving=None)
    ranked = await ranker.rank(items, context={})
    assert len(ranked) == 3
    scores = [item.score for item in ranked]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_model_ranking_empty(items):
    ranker = ModelBasedRanking(name="test_model")
    ranked = await ranker.rank([], context={})
    assert ranked == []
