"""Async Redis client for caching and key-value operations."""

from __future__ import annotations

from redis.asyncio import ConnectionPool, Redis

from fastrs.log import get_logger

logger = get_logger(__name__)


class RedisManager:
    """Manage an async Redis connection pool for cache / key-value operations.

    For message queue functionality see the :mod:`fastrs.mq` package.
    """

    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None

    # -- lifecycle -------------------------------------------------------------

    async def connect(
        self,
        url: str = "redis://localhost:6379/0",
        *,
        max_connections: int = 20,
    ) -> None:
        """Create a connection pool and Redis client.

        Args:
            url: Redis connection URL, e.g. ``redis://localhost:6379/0``.
            max_connections: Maximum number of pooled connections.
        """
        self._pool = ConnectionPool.from_url(url, max_connections=max_connections, decode_responses=True)
        self._client = Redis(connection_pool=self._pool)
        logger.info("redis_connected", url=url)

    async def disconnect(self) -> None:
        """Close the Redis connection and release the pool."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        if self._pool is not None:
            await self._pool.aclose()
            self._pool = None
        logger.info("redis_disconnected")

    # -- client access ---------------------------------------------------------

    @property
    def client(self) -> Redis:
        """Return the underlying async Redis client."""
        if self._client is None:
            raise RuntimeError("RedisManager is not connected. Call connect() first.")
        return self._client

    # -- cache helpers ---------------------------------------------------------

    async def get(self, key: str) -> str | None:
        """Get a value by key."""
        return await self.client.get(key)

    async def set(self, key: str, value: str, *, expire: int | None = None) -> None:
        """Set a key-value pair with an optional TTL in seconds."""
        if expire is not None:
            await self.client.set(key, value, ex=expire)
        else:
            await self.client.set(key, value)

    async def delete(self, key: str) -> None:
        """Delete a key."""
        await self.client.delete(key)

    # -- health ----------------------------------------------------------------

    async def ping(self) -> bool:
        """Return ``True`` if Redis is reachable."""
        if self._client is None:
            return False
        try:
            return await self._client.ping()
        except Exception:
            return False
