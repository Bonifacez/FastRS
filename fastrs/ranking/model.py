from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from fastrs.logging import get_logger
from fastrs.models.schemas import Item
from fastrs.ranking.base import BaseRanking

logger = get_logger("fastrs.ranking.model")

try:
    from fastrs.models.torch.serving import ModelServing
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class ModelBasedRanking(BaseRanking):
    """
    Model-based ranking using a PyTorch model for scoring.
    Falls back to base score if model is unavailable.
    """

    name: str = "model_ranking"

    def __init__(
        self,
        name: str = "model_ranking",
        serving: Optional[Any] = None,
        feature_dim: int = 64,
    ) -> None:
        self.name = name
        self.serving: Optional[Any] = serving
        self.feature_dim = feature_dim

    def _extract_features(self, item: Item, context: Dict[str, Any]) -> np.ndarray:
        """Extract feature vector for item+context pair."""
        features = np.zeros(self.feature_dim, dtype=np.float32)
        # Use item score as first feature
        features[0] = item.score
        # Use metadata features if present
        if item.metadata:
            if "popularity" in item.metadata:
                features[1] = float(item.metadata["popularity"])
            if "timestamp" in item.metadata:
                import time
                age = (time.time() - item.metadata["timestamp"]) / (3600 * 24)
                features[2] = max(0.0, 1.0 - age / 30)
        return features

    async def rank(self, items: List[Item], context: Dict[str, Any]) -> List[Item]:
        if not items:
            return items

        if self.serving is None or not TORCH_AVAILABLE:
            # Fallback: sort by base score
            return sorted(items, key=lambda x: x.score, reverse=True)

        try:
            features = np.array([
                self._extract_features(item, context) for item in items
            ], dtype=np.float32)
            scores = await self.serving.infer(features)
            scores = scores.flatten()

            ranked = sorted(
                zip(items, scores),
                key=lambda x: float(x[1]),
                reverse=True,
            )
            return [
                Item(item_id=item.item_id, score=float(score), metadata=item.metadata)
                for item, score in ranked
            ]
        except Exception as e:
            logger.error("model_ranking_error", error=str(e))
            return sorted(items, key=lambda x: x.score, reverse=True)
