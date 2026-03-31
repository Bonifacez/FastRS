from __future__ import annotations

from fastrs.recall.base import BaseRecall
from fastrs.recall.vector import VectorRecall
from fastrs.recall.collaborative import CollaborativeRecall
from fastrs.recall.registry import RecallRegistry, get_recall_registry

__all__ = ["BaseRecall", "VectorRecall", "CollaborativeRecall", "RecallRegistry", "get_recall_registry"]
