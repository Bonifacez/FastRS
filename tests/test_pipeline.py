"""Tests for the pipeline module."""

from fastrs.pipeline.loader import InMemoryLoader
from fastrs.pipeline.transform import DefaultValueFiller, FieldSelector


def test_in_memory_loader() -> None:
    data = [{"id": "1", "name": "A"}, {"id": "2", "name": "B"}]
    loader = InMemoryLoader(data)
    result = loader.execute()
    assert len(result) == 2
    assert result[0]["id"] == "1"


def test_field_selector() -> None:
    data = [{"id": "1", "name": "A", "extra": "x"}]
    selector = FieldSelector(["id", "name"])
    result = selector.execute(data)
    assert "extra" not in result[0]
    assert result[0]["name"] == "A"


def test_default_value_filler() -> None:
    data = [{"id": "1"}]
    filler = DefaultValueFiller({"score": 0.0, "tags": []})
    result = filler.execute(data)
    assert result[0]["score"] == 0.0
    assert result[0]["tags"] == []
