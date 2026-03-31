"""In-memory async message queue — simple, reliable, zero external dependencies."""

from __future__ import annotations

import asyncio
from typing import Any

from fastrs.log import get_logger
from fastrs.mq.base import BaseMessageQueue, MessageHandler

logger = get_logger(__name__)


class InMemoryMessageQueue(BaseMessageQueue):
    """A lightweight in-process message queue built on :class:`asyncio.Queue`.

    * Messages are buffered per-topic and never dropped while the process
      is alive.
    * Each topic can have **one** handler; subscribing again replaces the
      previous handler.
    * Useful as the default MQ backend for development and single-process
      deployments.
    """

    def __init__(self, maxsize: int = 0) -> None:
        self._maxsize = maxsize
        self._queues: dict[str, asyncio.Queue[dict[str, Any]]] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}

    # -- publish / subscribe ---------------------------------------------------

    async def publish(self, topic: str, message: dict[str, Any]) -> None:
        queue = self._queues.get(topic)
        if queue is None:
            # No subscriber yet — create the queue so messages buffer up.
            queue = asyncio.Queue(maxsize=self._maxsize)
            self._queues[topic] = queue
        await queue.put(message)
        logger.debug("mq_published", topic=topic)

    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        # Ensure a queue exists for this topic.
        if topic not in self._queues:
            self._queues[topic] = asyncio.Queue(maxsize=self._maxsize)

        # Cancel existing listener if re-subscribing.
        old_task = self._tasks.pop(topic, None)
        if old_task is not None:
            old_task.cancel()

        task = asyncio.create_task(self._consume(topic, handler))
        self._tasks[topic] = task
        logger.info("mq_subscribed", topic=topic)

    async def unsubscribe(self, topic: str) -> None:
        task = self._tasks.pop(topic, None)
        if task is not None:
            task.cancel()
            logger.info("mq_unsubscribed", topic=topic)

    async def close(self) -> None:
        for topic in list(self._tasks):
            await self.unsubscribe(topic)
        self._queues.clear()
        logger.info("mq_closed")

    # -- internals -------------------------------------------------------------

    async def _consume(self, topic: str, handler: MessageHandler) -> None:
        queue = self._queues[topic]
        try:
            while True:
                message = await queue.get()
                try:
                    await handler(topic, message)
                except Exception:
                    logger.exception("mq_handler_error", topic=topic)
                finally:
                    queue.task_done()
        except asyncio.CancelledError:
            pass
