"""Built-in data loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastrs.pipeline.base import DataLoader


class JSONFileLoader(DataLoader):
    """Load items from a JSON file."""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

    def execute(self, data: Any = None, **kwargs: Any) -> list[dict[str, Any]]:
        with open(self.file_path) as fh:
            return json.load(fh)


class InMemoryLoader(DataLoader):
    """Wrap an in-memory list of dicts so it conforms to the loader interface."""

    def __init__(self, items: list[dict[str, Any]] | None = None) -> None:
        self.items: list[dict[str, Any]] = items or []

    def execute(self, data: Any = None, **kwargs: Any) -> list[dict[str, Any]]:
        return list(self.items)
