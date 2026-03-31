"""Tests for RedisManager (without a real Redis server)."""

from __future__ import annotations

import pytest

from fastrs.db.redis import RedisManager


def test_redis_manager_not_connected() -> None:
    mgr = RedisManager()
    with pytest.raises(RuntimeError, match="not connected"):
        _ = mgr.client


@pytest.mark.asyncio
async def test_redis_ping_when_not_connected() -> None:
    mgr = RedisManager()
    assert await mgr.ping() is False


@pytest.mark.asyncio
async def test_redis_disconnect_when_not_connected() -> None:
    mgr = RedisManager()
    # Should not raise
    await mgr.disconnect()
