from __future__ import annotations

import pytest

from fastrs.models.schemas import Item
from fastrs.filter.dedup import DedupFilter
from fastrs.filter.blacklist import BlacklistFilter


@pytest.fixture
def items_with_dupes():
    return [
        Item(item_id="a", score=0.9),
        Item(item_id="b", score=0.5),
        Item(item_id="a", score=0.7),  # Duplicate - lower score
        Item(item_id="c", score=0.3),
        Item(item_id="b", score=0.8),  # Duplicate - higher score
    ]


@pytest.mark.asyncio
async def test_dedup_filter_removes_duplicates(items_with_dupes):
    filt = DedupFilter()
    result = await filt.filter(items_with_dupes)
    ids = [item.item_id for item in result]
    assert len(ids) == len(set(ids))
    assert len(result) == 3


@pytest.mark.asyncio
async def test_dedup_filter_keeps_highest_score(items_with_dupes):
    filt = DedupFilter()
    result = await filt.filter(items_with_dupes)
    id_to_score = {item.item_id: item.score for item in result}
    assert id_to_score["a"] == 0.9
    assert id_to_score["b"] == 0.8


@pytest.mark.asyncio
async def test_dedup_filter_empty():
    filt = DedupFilter()
    result = await filt.filter([])
    assert result == []


@pytest.mark.asyncio
async def test_blacklist_filter_removes_blocked():
    items = [
        Item(item_id="a", score=0.9),
        Item(item_id="b", score=0.5),
        Item(item_id="c", score=0.3),
    ]
    filt = BlacklistFilter(blacklist={"b"})
    result = await filt.filter(items)
    ids = [item.item_id for item in result]
    assert "b" not in ids
    assert "a" in ids
    assert "c" in ids


@pytest.mark.asyncio
async def test_blacklist_filter_add_remove():
    items = [Item(item_id="x", score=1.0), Item(item_id="y", score=0.5)]
    filt = BlacklistFilter()
    filt.add("x")
    result = await filt.filter(items)
    assert all(item.item_id != "x" for item in result)

    filt.remove("x")
    result2 = await filt.filter(items)
    ids = [item.item_id for item in result2]
    assert "x" in ids


@pytest.mark.asyncio
async def test_blacklist_filter_empty():
    filt = BlacklistFilter()
    items = [Item(item_id="a", score=0.9)]
    result = await filt.filter(items)
    assert len(result) == 1
