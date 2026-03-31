from __future__ import annotations

import asyncio

import numpy as np
import pytest

from fastrs.pipeline.registry import PipelineRegistry
from fastrs.pipeline.data import DataPipeline
from fastrs.recall.vector import VectorRecall
from fastrs.ranking.rule import RuleBasedRanking
from fastrs.filter.dedup import DedupFilter
from fastrs.models.schemas import RecommendRequest


@pytest.fixture
def vector_recall():
    vr = VectorRecall(embedding_dim=8, name="vr")
    rng = np.random.default_rng(1)
    for i in range(30):
        vr.add_item(f"item_{i}", rng.standard_normal(8).astype(np.float32))
    return vr


@pytest.fixture
def rule_ranker():
    return RuleBasedRanking(name="rr")


@pytest.fixture
def dedup():
    return DedupFilter(name="dd")


@pytest.fixture
def pipeline(vector_recall, rule_ranker, dedup):
    return DataPipeline(
        name="test_pipe",
        recall_module=vector_recall,
        ranking_module=rule_ranker,
        filter_modules=[dedup],
    )


@pytest.mark.asyncio
async def test_registry_add_and_get(pipeline):
    registry = PipelineRegistry()
    await registry.add(pipeline)
    p = await registry.get("test_pipe")
    assert p is not None
    assert p.name == "test_pipe"


@pytest.mark.asyncio
async def test_registry_list(pipeline):
    registry = PipelineRegistry()
    await registry.add(pipeline)
    listing = await registry.list()
    assert any(p["name"] == "test_pipe" for p in listing)


@pytest.mark.asyncio
async def test_registry_remove(pipeline):
    registry = PipelineRegistry()
    await registry.add(pipeline)
    removed = await registry.remove("test_pipe")
    assert removed is True
    p = await registry.get("test_pipe")
    assert p is None


@pytest.mark.asyncio
async def test_registry_remove_nonexistent():
    registry = PipelineRegistry()
    result = await registry.remove("nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_pipeline_process(pipeline):
    request = RecommendRequest(user_id="user_1", top_k=5)
    response = await pipeline.process(request)
    assert response.user_id == "user_1"
    assert len(response.items) <= 5
    assert response.pipeline == "test_pipe"
    assert response.latency_ms is not None


@pytest.mark.asyncio
async def test_hot_swap(vector_recall, rule_ranker):
    registry = PipelineRegistry()
    old_pipe = DataPipeline(name="swap_test", recall_module=vector_recall, ranking_module=rule_ranker)
    await registry.add(old_pipe)

    new_pipe = DataPipeline(name="swap_test", recall_module=vector_recall, ranking_module=rule_ranker)
    swapped = await registry.hot_swap("swap_test", new_pipe)
    assert swapped is True

    p = await registry.get("swap_test")
    assert p is new_pipe


@pytest.mark.asyncio
async def test_registry_restart(pipeline):
    registry = PipelineRegistry()
    await registry.add(pipeline)
    restarted = await registry.restart("test_pipe")
    assert restarted is True
