"""Built-in data transformers."""

from __future__ import annotations

from typing import Any

from fastrs.pipeline.base import DataTransformer


class FieldSelector(DataTransformer):
    """Keep only specified fields from each item dict."""

    def __init__(self, fields: list[str]) -> None:
        self.fields = fields

    def execute(self, data: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
        return [{k: item.get(k) for k in self.fields} for item in data]


class DefaultValueFiller(DataTransformer):
    """Fill missing keys with default values."""

    def __init__(self, defaults: dict[str, Any]) -> None:
        self.defaults = defaults

    def execute(self, data: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
        for item in data:
            for key, default in self.defaults.items():
                item.setdefault(key, default)
        return data
