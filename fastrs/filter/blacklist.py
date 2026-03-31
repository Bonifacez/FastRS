from __future__ import annotations

from typing import List, Set

from fastrs.models.schemas import Item
from fastrs.filter.base import BaseFilter


class BlacklistFilter(BaseFilter):
    """Filter out blacklisted items."""

    name: str = "blacklist_filter"

    def __init__(self, name: str = "blacklist_filter", blacklist: Set[str] | None = None) -> None:
        self.name = name
        self._blacklist: Set[str] = blacklist or set()

    def add(self, item_id: str) -> None:
        self._blacklist.add(item_id)

    def remove(self, item_id: str) -> None:
        self._blacklist.discard(item_id)

    def clear(self) -> None:
        self._blacklist.clear()

    @property
    def blacklist(self) -> Set[str]:
        return frozenset(self._blacklist)

    async def filter(self, items: List[Item]) -> List[Item]:
        return [item for item in items if item.item_id not in self._blacklist]
