"""Tests for ranking strategies."""

from fastrs.core.types import ItemScore
from fastrs.ranking.score import PassThroughRanker, WeightedFieldRanker


def test_passthrough_ranker() -> None:
    items = [
        ItemScore(item_id="a", score=1.0),
        ItemScore(item_id="b", score=5.0),
        ItemScore(item_id="c", score=3.0),
    ]
    ranker = PassThroughRanker()
    ranked = ranker.rank("user1", items)
    assert ranked[0].item_id == "b"
    assert ranked[1].item_id == "c"
    assert ranked[2].item_id == "a"


def test_weighted_field_ranker() -> None:
    items = [
        ItemScore(item_id="a", score=0, metadata={"rating": 4.0, "popularity": 100}),
        ItemScore(item_id="b", score=0, metadata={"rating": 5.0, "popularity": 10}),
    ]
    ranker = WeightedFieldRanker({"rating": 1.0, "popularity": 0.01})
    ranked = ranker.rank("user1", items)
    # a: 4.0*1 + 100*0.01 = 5.0, b: 5.0*1 + 10*0.01 = 5.1
    assert ranked[0].item_id == "b"
