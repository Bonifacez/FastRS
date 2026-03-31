"""Tests for the in-memory message queue."""

from __future__ import annotations

import asyncio

import pytest

from fastrs.mq.memory import InMemoryMessageQueue


@pytest.mark.asyncio
async def test_publish_and_subscribe() -> None:
    mq = InMemoryMessageQueue()
    received: list[dict] = []

    async def handler(topic: str, message: dict) -> None:
        received.append(message)

    await mq.subscribe("test-topic", handler)
    await mq.publish("test-topic", {"key": "value"})

    # Give the consumer task a moment to process
    await asyncio.sleep(0.05)

    assert len(received) == 1
    assert received[0] == {"key": "value"}

    await mq.close()


@pytest.mark.asyncio
async def test_multiple_messages() -> None:
    mq = InMemoryMessageQueue()
    received: list[dict] = []

    async def handler(topic: str, message: dict) -> None:
        received.append(message)

    await mq.subscribe("orders", handler)

    for i in range(5):
        await mq.publish("orders", {"id": i})

    await asyncio.sleep(0.1)
    assert len(received) == 5
    assert [m["id"] for m in received] == [0, 1, 2, 3, 4]

    await mq.close()


@pytest.mark.asyncio
async def test_unsubscribe() -> None:
    mq = InMemoryMessageQueue()
    received: list[dict] = []

    async def handler(topic: str, message: dict) -> None:
        received.append(message)

    await mq.subscribe("events", handler)
    await mq.publish("events", {"n": 1})
    await asyncio.sleep(0.05)

    await mq.unsubscribe("events")
    await mq.publish("events", {"n": 2})
    await asyncio.sleep(0.05)

    # Only the first message should have been received
    assert len(received) == 1

    await mq.close()


@pytest.mark.asyncio
async def test_publish_before_subscribe_buffers() -> None:
    mq = InMemoryMessageQueue()
    received: list[dict] = []

    # Publish first — messages should buffer in the queue
    await mq.publish("buf", {"a": 1})
    await mq.publish("buf", {"a": 2})

    async def handler(topic: str, message: dict) -> None:
        received.append(message)

    await mq.subscribe("buf", handler)
    await asyncio.sleep(0.1)

    assert len(received) == 2

    await mq.close()


@pytest.mark.asyncio
async def test_handler_error_does_not_crash_consumer() -> None:
    mq = InMemoryMessageQueue()
    received: list[dict] = []

    async def handler(topic: str, message: dict) -> None:
        if message.get("fail"):
            raise ValueError("boom")
        received.append(message)

    await mq.subscribe("err", handler)
    await mq.publish("err", {"fail": True})
    await mq.publish("err", {"ok": True})
    await asyncio.sleep(0.1)

    # The second message should still be processed
    assert len(received) == 1
    assert received[0] == {"ok": True}

    await mq.close()


@pytest.mark.asyncio
async def test_close_cancels_all() -> None:
    mq = InMemoryMessageQueue()

    async def handler(topic: str, message: dict) -> None:
        pass  # pragma: no cover

    await mq.subscribe("a", handler)
    await mq.subscribe("b", handler)
    await mq.close()

    # Internal state should be cleared
    assert len(mq._tasks) == 0
    assert len(mq._queues) == 0
