"""Async PostgreSQL connection management via SQLAlchemy."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from fastrs.log import get_logger

logger = get_logger(__name__)


class PostgresManager:
    """Manage an async PostgreSQL connection pool.

    Uses SQLAlchemy's async engine backed by ``asyncpg``.
    """

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    # -- lifecycle -------------------------------------------------------------

    async def connect(
        self,
        dsn: str,
        *,
        pool_size: int = 10,
        max_overflow: int = 20,
        echo: bool = False,
    ) -> None:
        """Create the async engine and session factory.

        Args:
            dsn: PostgreSQL connection string,
                 e.g. ``postgresql+asyncpg://user:pass@host:5432/db``.
            pool_size: Number of persistent connections in the pool.
            max_overflow: Max extra connections beyond *pool_size*.
            echo: If ``True``, log all SQL statements.
        """
        self._engine = create_async_engine(
            dsn,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=echo,
        )
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)
        logger.info("postgres_connected", pool_size=pool_size)

    async def disconnect(self) -> None:
        """Dispose of the engine and release all pooled connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("postgres_disconnected")

    # -- session helpers -------------------------------------------------------

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("PostgresManager is not connected. Call connect() first.")
        return self._engine

    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield an ``AsyncSession`` (use as an async context manager / generator)."""
        if self._session_factory is None:
            raise RuntimeError("PostgresManager is not connected. Call connect() first.")
        async with self._session_factory() as sess:
            yield sess

    # -- health ----------------------------------------------------------------

    async def ping(self) -> bool:
        """Return ``True`` if the database is reachable."""
        if self._engine is None:
            return False
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
