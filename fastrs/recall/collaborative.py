from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from fastrs.logging import get_logger
from fastrs.models.schemas import Item
from fastrs.recall.base import BaseRecall

logger = get_logger("fastrs.recall.collaborative")


class CollaborativeRecall(BaseRecall):
    """Item-item collaborative filtering recall."""

    name: str = "collaborative_recall"

    def __init__(self, name: str = "collaborative_recall") -> None:
        self.name = name
        # user_id -> {item_id -> rating}
        self._interactions: Dict[str, Dict[str, float]] = {}
        # item_id list
        self._items: List[str] = []
        self._item_index: Dict[str, int] = {}
        self._similarity_matrix: Optional[np.ndarray] = None
        self._dirty: bool = False

    def add_interaction(self, user_id: str, item_id: str, rating: float = 1.0) -> None:
        if user_id not in self._interactions:
            self._interactions[user_id] = {}
        self._interactions[user_id][item_id] = rating
        if item_id not in self._item_index:
            self._item_index[item_id] = len(self._items)
            self._items.append(item_id)
        self._dirty = True

    def _build_matrix(self) -> None:
        n_users = len(self._interactions)
        n_items = len(self._items)
        if n_users == 0 or n_items == 0:
            self._similarity_matrix = None
            return

        # Build user-item matrix
        matrix = np.zeros((n_users, n_items), dtype=np.float32)
        for u_idx, (_, ratings) in enumerate(self._interactions.items()):
            for item_id, rating in ratings.items():
                i_idx = self._item_index[item_id]
                matrix[u_idx, i_idx] = rating

        # Item-item cosine similarity
        norms = np.linalg.norm(matrix, axis=0, keepdims=True) + 1e-10
        normed = matrix / norms
        self._similarity_matrix = normed.T @ normed
        self._dirty = False

    async def recall(self, query: str, context: Dict[str, Any], top_k: int) -> List[Item]:
        if self._dirty or self._similarity_matrix is None:
            self._build_matrix()

        if self._similarity_matrix is None:
            return []

        user_items = self._interactions.get(query, {})
        if not user_items:
            # Cold start: return popular items
            n_items = len(self._items)
            popularity = np.zeros(n_items, dtype=np.float32)
            for ratings in self._interactions.values():
                for item_id, rating in ratings.items():
                    popularity[self._item_index[item_id]] += rating
            k = min(top_k, n_items)
            top_indices = np.argpartition(popularity, -k)[-k:]
            top_indices = top_indices[np.argsort(popularity[top_indices])[::-1]]
            return [Item(item_id=self._items[i], score=float(popularity[i])) for i in top_indices]

        # Aggregate scores from interacted items
        scores = np.zeros(len(self._items), dtype=np.float32)
        seen = set()
        for item_id, rating in user_items.items():
            seen.add(item_id)
            if item_id not in self._item_index:
                continue
            i_idx = self._item_index[item_id]
            scores += self._similarity_matrix[i_idx] * rating

        # Zero out already seen
        for item_id in seen:
            if item_id in self._item_index:
                scores[self._item_index[item_id]] = 0.0

        k = min(top_k, len(scores))
        if k == 0:
            return []
        top_indices = np.argpartition(scores, -k)[-k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
        return [Item(item_id=self._items[i], score=float(scores[i])) for i in top_indices if scores[i] > 0]
