"""Abstract base class for message queues."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine

MessageHandler = Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]]


class BaseMessageQueue(ABC):
    """Abstract async message queue.

    Implementations must support:

    * **publish** — put a message onto a named topic.
    * **subscribe** — register an async handler that receives messages
      from a topic.  The handler runs in a background task.
    * **unsubscribe** — stop receiving messages from a topic.
    * **close** — clean up all resources.
    """

    @abstractmethod
    async def publish(self, topic: str, message: dict[str, Any]) -> None:
        """Publish *message* to *topic*."""

    @abstractmethod
    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        """Subscribe *handler* to *topic*.

        ``handler`` signature: ``async def handler(topic: str, message: dict) -> None``
        """

    @abstractmethod
    async def unsubscribe(self, topic: str) -> None:
        """Stop the subscription for *topic*."""

    @abstractmethod
    async def close(self) -> None:
        """Release all resources (cancel listeners, close connections)."""
