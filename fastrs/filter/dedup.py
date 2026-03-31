from __future__ import annotations

from typing import List

from fastrs.models.schemas import Item
from fastrs.filter.base import BaseFilter


class DedupFilter(BaseFilter):
    """Remove duplicate items (by item_id), keeping the highest-scored."""

    name: str = "dedup_filter"

    def __init__(self, name: str = "dedup_filter") -> None:
        self.name = name

    async def filter(self, items: List[Item]) -> List[Item]:
        seen: dict[str, Item] = {}
        for item in items:
            if item.item_id not in seen or item.score > seen[item.item_id].score:
                seen[item.item_id] = item
        # Preserve original order (first occurrence, highest score wins)
        result = list(seen.values())
        return sorted(result, key=lambda x: x.score, reverse=True)
