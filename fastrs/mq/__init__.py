"""Message queue package.

Provides a simple, reliable async message queue abstraction with two backends:

* :class:`~fastrs.mq.memory.InMemoryMessageQueue` — zero-dependency,
  in-process queue (default).  Messages are buffered in ``asyncio.Queue``
  and never lost while the process is alive.

* :class:`~fastrs.mq.redis_stream.RedisStreamMessageQueue` — persistent
  queue backed by Redis Streams (``XADD`` / ``XREADGROUP``).  Supports
  consumer groups and message acknowledgement for at-least-once delivery.
"""
