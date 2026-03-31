"""Tests for PostgresManager (without a real database)."""

from __future__ import annotations

import pytest

from fastrs.db.postgres import PostgresManager


def test_postgres_manager_not_connected() -> None:
    pg = PostgresManager()
    with pytest.raises(RuntimeError, match="not connected"):
        _ = pg.engine


@pytest.mark.asyncio
async def test_postgres_ping_when_not_connected() -> None:
    pg = PostgresManager()
    assert await pg.ping() is False


@pytest.mark.asyncio
async def test_postgres_session_when_not_connected() -> None:
    pg = PostgresManager()
    with pytest.raises(RuntimeError, match="not connected"):
        async for _ in pg.session():
            pass  # pragma: no cover
