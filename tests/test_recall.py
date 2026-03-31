"""Tests for recall strategies."""

from fastrs.core.types import ItemScore
from fastrs.recall.popular import PopularityRecall, RandomRecall


def test_popularity_recall() -> None:
    scores = {"a": 10.0, "b": 5.0, "c": 8.0, "d": 1.0}
    recall = PopularityRecall(scores)
    results = recall.recall("user1", top_k=2)
    assert len(results) == 2
    assert results[0].item_id == "a"
    assert results[1].item_id == "c"


def test_popularity_recall_empty() -> None:
    recall = PopularityRecall()
    results = recall.recall("user1", top_k=5)
    assert results == []


def test_random_recall() -> None:
    ids = [f"item_{i}" for i in range(20)]
    recall = RandomRecall(ids, seed=42)
    results = recall.recall("user1", top_k=5)
    assert len(results) == 5
    assert all(isinstance(r, ItemScore) for r in results)


def test_random_recall_top_k_larger_than_pool() -> None:
    ids = ["a", "b"]
    recall = RandomRecall(ids, seed=0)
    results = recall.recall("user1", top_k=100)
    assert len(results) == 2
