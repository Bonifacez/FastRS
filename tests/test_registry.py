"""Tests for the module registry."""

import pytest

from fastrs.core.registry import ModuleRegistry
from fastrs.core.types import ModuleType


class DummyModule:
    pass


def test_register_and_get(registry: ModuleRegistry) -> None:
    mod = DummyModule()
    registry.register("test", ModuleType.RECALL, mod)
    assert registry.get("test") is mod


def test_register_duplicate(registry: ModuleRegistry) -> None:
    registry.register("dup", ModuleType.RECALL, DummyModule())
    with pytest.raises(ValueError, match="already registered"):
        registry.register("dup", ModuleType.RECALL, DummyModule())


def test_unregister(registry: ModuleRegistry) -> None:
    registry.register("rm", ModuleType.RECALL, DummyModule())
    registry.unregister("rm")
    with pytest.raises(KeyError):
        registry.get("rm")


def test_unregister_missing(registry: ModuleRegistry) -> None:
    with pytest.raises(KeyError):
        registry.unregister("missing")


def test_enable_disable(registry: ModuleRegistry) -> None:
    registry.register("toggle", ModuleType.RANKING, DummyModule())
    registry.disable("toggle")
    info = registry.get_info("toggle")
    assert not info.enabled

    registry.enable("toggle")
    info = registry.get_info("toggle")
    assert info.enabled


def test_restart(registry: ModuleRegistry) -> None:
    old = DummyModule()
    new = DummyModule()
    registry.register("swap", ModuleType.FILTER, old)
    assert registry.get("swap") is old
    registry.restart("swap", new)
    assert registry.get("swap") is new


def test_list_modules(registry: ModuleRegistry) -> None:
    registry.register("r1", ModuleType.RECALL, DummyModule())
    registry.register("r2", ModuleType.RANKING, DummyModule())
    registry.register("r3", ModuleType.RECALL, DummyModule())
    registry.disable("r3")

    all_mods = registry.list_modules()
    assert len(all_mods) == 3

    recall_mods = registry.list_modules(module_type=ModuleType.RECALL)
    assert len(recall_mods) == 2

    enabled_recall = registry.list_modules(module_type=ModuleType.RECALL, enabled_only=True)
    assert len(enabled_recall) == 1


def test_get_instances(registry: ModuleRegistry) -> None:
    m1, m2 = DummyModule(), DummyModule()
    registry.register("a", ModuleType.RECALL, m1)
    registry.register("b", ModuleType.RECALL, m2)
    registry.register("c", ModuleType.RANKING, DummyModule())

    instances = registry.get_instances(ModuleType.RECALL)
    assert len(instances) == 2
    assert instances["a"] is m1
