"""Tests for filter rules."""

from fastrs.core.types import ItemScore
from fastrs.filter.rules import ExcludeItemsFilter, MinScoreFilter


def test_exclude_items_filter() -> None:
    items = [
        ItemScore(item_id="a", score=1.0),
        ItemScore(item_id="b", score=2.0),
        ItemScore(item_id="c", score=3.0),
    ]
    filt = ExcludeItemsFilter(excluded_ids={"b"})
    result = filt.apply("user1", items)
    assert len(result) == 2
    assert all(i.item_id != "b" for i in result)


def test_exclude_from_context() -> None:
    items = [ItemScore(item_id="x", score=1.0), ItemScore(item_id="y", score=2.0)]
    filt = ExcludeItemsFilter()
    result = filt.apply("user1", items, context={"exclude_ids": ["x"]})
    assert len(result) == 1
    assert result[0].item_id == "y"


def test_min_score_filter() -> None:
    items = [
        ItemScore(item_id="a", score=0.1),
        ItemScore(item_id="b", score=0.5),
        ItemScore(item_id="c", score=0.9),
    ]
    filt = MinScoreFilter(min_score=0.5)
    result = filt.apply("user1", items)
    assert len(result) == 2
    assert result[0].item_id == "b"
