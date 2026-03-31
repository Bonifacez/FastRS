from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from fastrs.logging import get_logger

logger = get_logger("fastrs.middleware")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class LatencyMiddleware(BaseHTTPMiddleware):
    """Track and log request latency."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Latency-Ms"] = f"{latency_ms:.3f}"
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=round(latency_ms, 3),
            request_id=request_id,
        )
        return response
