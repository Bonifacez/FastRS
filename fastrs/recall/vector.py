from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from fastrs.logging import get_logger
from fastrs.models.schemas import Item
from fastrs.recall.base import BaseRecall

logger = get_logger("fastrs.recall.vector")


class VectorRecall(BaseRecall):
    """ANN-based recall using cosine similarity over a numpy embedding matrix."""

    name: str = "vector_recall"

    def __init__(self, embedding_dim: int = 64, name: str = "vector_recall") -> None:
        self.name = name
        self.embedding_dim = embedding_dim
        self._item_ids: List[str] = []
        self._embeddings: Optional[np.ndarray] = None
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def add_item(
        self,
        item_id: str,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._item_ids.append(item_id)
        emb = embedding.reshape(1, -1).astype(np.float32)
        if self._embeddings is None:
            self._embeddings = emb
        else:
            self._embeddings = np.vstack([self._embeddings, emb])
        if metadata:
            self._metadata[item_id] = metadata

    def add_items_batch(
        self,
        item_ids: List[str],
        embeddings: np.ndarray,
        metadata: Optional[List[Optional[Dict[str, Any]]]] = None,
    ) -> None:
        for i, (item_id, emb) in enumerate(zip(item_ids, embeddings)):
            meta = metadata[i] if metadata else None
            self.add_item(item_id, emb, meta)

    def _cosine_similarity(self, query_vec: np.ndarray) -> np.ndarray:
        if self._embeddings is None or len(self._embeddings) == 0:
            return np.array([])
        q = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True) + 1e-10
        normed = self._embeddings / norms
        return (normed @ q).flatten()

    async def recall(self, query: str, context: Dict[str, Any], top_k: int) -> List[Item]:
        if self._embeddings is None or len(self._item_ids) == 0:
            logger.warning("vector_recall_empty", query=query)
            return []

        # Use query embedding from context, else random (demo purpose)
        if "query_embedding" in context:
            query_vec = np.array(context["query_embedding"], dtype=np.float32)
        else:
            rng = np.random.default_rng(abs(hash(query)) % (2**31))
            query_vec = rng.standard_normal(self.embedding_dim).astype(np.float32)

        scores = self._cosine_similarity(query_vec)
        k = min(top_k, len(scores))
        top_indices = np.argpartition(scores, -k)[-k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        items = []
        for idx in top_indices:
            item_id = self._item_ids[idx]
            items.append(Item(
                item_id=item_id,
                score=float(scores[idx]),
                metadata=self._metadata.get(item_id),
            ))
        return items
