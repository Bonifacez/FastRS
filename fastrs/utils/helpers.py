"""Helper utilities for FastRS."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator

from fastrs.log import get_logger

logger = get_logger(__name__)


@contextmanager
def timer(label: str) -> Generator[None, None, None]:
    """Context manager that logs elapsed time."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    logger.info("timer", label=label, elapsed_seconds=round(elapsed, 4))
