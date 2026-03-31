"""Test fixtures for FastRS."""

from __future__ import annotations

import pytest

from fastrs.config import FastRSConfig
from fastrs.core.registry import ModuleRegistry


@pytest.fixture()
def config() -> FastRSConfig:
    return FastRSConfig()


@pytest.fixture()
def registry() -> ModuleRegistry:
    return ModuleRegistry()
