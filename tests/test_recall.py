from __future__ import annotations

import numpy as np
import pytest

from fastrs.recall.vector import VectorRecall
from fastrs.recall.collaborative import CollaborativeRecall


@pytest.fixture
def vector_recall():
    vr = VectorRecall(embedding_dim=8, name="test_vector")
    rng = np.random.default_rng(0)
    for i in range(20):
        emb = rng.standard_normal(8).astype(np.float32)
        vr.add_item(f"item_{i}", emb, metadata={"category": f"cat_{i % 3}"})
    return vr


@pytest.fixture
def collab_recall():
    cr = CollaborativeRecall(name="test_collab")
    for u in range(5):
        for i in range(10):
            cr.add_interaction(f"user_{u}", f"item_{(u + i) % 20}", float(i % 5 + 1))
    return cr


@pytest.mark.asyncio
async def test_vector_recall_returns_items(vector_recall):
    items = await vector_recall.recall("user_1", {}, top_k=5)
    assert len(items) == 5
    for item in items:
        assert item.item_id.startswith("item_")
        assert isinstance(item.score, float)


@pytest.mark.asyncio
async def test_vector_recall_with_embedding(vector_recall):
    rng = np.random.default_rng(99)
    query_emb = rng.standard_normal(8).tolist()
    items = await vector_recall.recall("user_1", {"query_embedding": query_emb}, top_k=3)
    assert len(items) == 3


@pytest.mark.asyncio
async def test_vector_recall_empty():
    vr = VectorRecall(embedding_dim=8)
    items = await vr.recall("user_1", {}, top_k=5)
    assert items == []


@pytest.mark.asyncio
async def test_collab_recall_known_user(collab_recall):
    items = await collab_recall.recall("user_0", {}, top_k=5)
    assert isinstance(items, list)
    # Should return non-seen items
    for item in items:
        assert item.item_id.startswith("item_")


@pytest.mark.asyncio
async def test_collab_recall_cold_start(collab_recall):
    # Unknown user -> cold start -> popular items
    items = await collab_recall.recall("new_user_999", {}, top_k=5)
    assert isinstance(items, list)
    assert len(items) <= 5


@pytest.mark.asyncio
async def test_collab_recall_scores_positive(collab_recall):
    items = await collab_recall.recall("user_1", {}, top_k=10)
    for item in items:
        assert item.score >= 0
