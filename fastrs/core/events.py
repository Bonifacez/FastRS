from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from fastrs.config import get_settings
from fastrs.logging import configure_logging, get_logger
from fastrs.pipeline.registry import get_pipeline_registry
from fastrs.recall.registry import get_recall_registry
from fastrs.ranking.registry import get_ranking_registry
from fastrs.filter.registry import get_filter_registry

logger = get_logger("fastrs.events")


async def _setup_default_modules() -> None:
    """Set up default recall, ranking, filter, and pipeline modules."""
    import numpy as np

    from fastrs.recall.vector import VectorRecall
    from fastrs.recall.collaborative import CollaborativeRecall
    from fastrs.ranking.rule import RuleBasedRanking
    from fastrs.filter.dedup import DedupFilter
    from fastrs.filter.blacklist import BlacklistFilter
    from fastrs.pipeline.data import DataPipeline

    recall_reg = get_recall_registry()
    ranking_reg = get_ranking_registry()
    filter_reg = get_filter_registry()
    pipeline_reg = get_pipeline_registry()

    # Vector recall with sample items
    vector_recall = VectorRecall(embedding_dim=64, name="vector_recall")
    rng = np.random.default_rng(42)
    item_ids = [f"item_{i}" for i in range(200)]
    embeddings = rng.standard_normal((200, 64)).astype(np.float32)
    vector_recall.add_items_batch(
        item_ids,
        embeddings,
        metadata=[{"popularity": rng.random(), "category": f"cat_{i % 5}"} for i in range(200)],
    )
    await recall_reg.add(vector_recall)

    # Collaborative recall with sample interactions
    collab_recall = CollaborativeRecall(name="collaborative_recall")
    for u in range(50):
        for i in rng.integers(0, 200, size=10):
            collab_recall.add_interaction(f"user_{u}", f"item_{i}", float(rng.integers(1, 6)))
    await recall_reg.add(collab_recall)

    # Rule-based ranking
    rule_ranking = RuleBasedRanking(name="rule_ranking")
    for item_id in item_ids:
        rule_ranking.set_popularity(item_id, rng.random())
    await ranking_reg.add(rule_ranking)

    # Filters
    dedup = DedupFilter(name="dedup_filter")
    await filter_reg.add(dedup)
    blacklist = BlacklistFilter(name="blacklist_filter")
    await filter_reg.add(blacklist)

    # Default pipeline
    default_pipeline = DataPipeline(
        name="default",
        recall_module=vector_recall,
        ranking_module=rule_ranking,
        filter_modules=[dedup, blacklist],
    )
    await pipeline_reg.add(default_pipeline)

    # Collaborative pipeline
    collab_pipeline = DataPipeline(
        name="collaborative",
        recall_module=collab_recall,
        ranking_module=rule_ranking,
        filter_modules=[dedup],
    )
    await pipeline_reg.add(collab_pipeline)

    logger.info("default_modules_ready")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    logger.info("fastrs_starting", version="0.1.0", host=settings.host, port=settings.port)

    await _setup_default_modules()

    logger.info("fastrs_ready")
    yield

    await get_pipeline_registry().shutdown_all()
    logger.info("fastrs_shutdown")
