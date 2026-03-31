"""Redis Streams-backed message queue — persistent, with consumer groups.

Unlike Redis Pub/Sub, Streams provide:

* **Persistence** — messages survive subscriber downtime.
* **Consumer groups** — multiple workers can share the load.
* **Acknowledgement** — at-least-once delivery via ``XACK``.
"""

from __future__ import annotations

import asyncio
from typing import Any

from redis.asyncio import Redis

from fastrs.log import get_logger
from fastrs.mq.base import BaseMessageQueue, MessageHandler

logger = get_logger(__name__)


class RedisStreamMessageQueue(BaseMessageQueue):
    """Message queue backed by Redis Streams (``XADD`` / ``XREADGROUP``).

    Args:
        redis: An already-connected async Redis client.
        group: Consumer-group name.  All instances sharing the same group
            participate in load-balanced consumption (each message is
            delivered to exactly one consumer in the group).
        consumer: Unique consumer name within the group (e.g. hostname).
    """

    def __init__(self, redis: Redis, *, group: str = "fastrs", consumer: str = "worker-0") -> None:
        self._redis = redis
        self._group = group
        self._consumer = consumer
        self._tasks: dict[str, asyncio.Task[None]] = {}

    # -- publish / subscribe ---------------------------------------------------

    async def publish(self, topic: str, message: dict[str, Any]) -> None:
        """Append *message* to the Redis Stream named *topic*."""
        # Flatten dict values to strings for Redis Stream fields.
        fields = {k: str(v) for k, v in message.items()}
        await self._redis.xadd(topic, fields)
        logger.debug("mq_stream_published", topic=topic)

    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        """Start consuming *topic* via a consumer group."""
        await self._ensure_group(topic)

        old = self._tasks.pop(topic, None)
        if old is not None:
            old.cancel()

        task = asyncio.create_task(self._consume(topic, handler))
        self._tasks[topic] = task
        logger.info("mq_stream_subscribed", topic=topic, group=self._group, consumer=self._consumer)

    async def unsubscribe(self, topic: str) -> None:
        task = self._tasks.pop(topic, None)
        if task is not None:
            task.cancel()
            logger.info("mq_stream_unsubscribed", topic=topic)

    async def close(self) -> None:
        for topic in list(self._tasks):
            await self.unsubscribe(topic)
        logger.info("mq_stream_closed")

    # -- internals -------------------------------------------------------------

    async def _ensure_group(self, topic: str) -> None:
        """Create the consumer group if it doesn't exist yet."""
        try:
            await self._redis.xgroup_create(topic, self._group, id="0", mkstream=True)
        except Exception:
            # Group already exists — that's fine.
            pass

    async def _consume(self, topic: str, handler: MessageHandler) -> None:
        """Read new messages from the stream in a loop."""
        try:
            while True:
                entries = await self._redis.xreadgroup(
                    groupname=self._group,
                    consumername=self._consumer,
                    streams={topic: ">"},
                    count=10,
                    block=5000,
                )
                if not entries:
                    continue
                for _stream, messages in entries:
                    for msg_id, fields in messages:
                        try:
                            await handler(topic, dict(fields))
                            await self._redis.xack(topic, self._group, msg_id)
                        except Exception:
                            logger.exception("mq_stream_handler_error", topic=topic, msg_id=msg_id)
        except asyncio.CancelledError:
            pass
