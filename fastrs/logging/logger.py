from __future__ import annotations

import logging
import sys
import time
from typing import Any

import structlog


def configure_logging(log_level: str = "INFO", log_json: bool = False) -> None:
    log_level_num = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if log_json:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level_num)


def get_logger(name: str = "fastrs") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


class RequestLogger:
    def __init__(self) -> None:
        self._logger = get_logger("fastrs.request")

    def log_request(
        self,
        request_id: str,
        method: str,
        path: str,
        user_id: str | None = None,
        latency_ms: float | None = None,
        status_code: int | None = None,
        **kwargs: Any,
    ) -> None:
        self._logger.info(
            "request",
            request_id=request_id,
            method=method,
            path=path,
            user_id=user_id,
            latency_ms=latency_ms,
            status_code=status_code,
            **kwargs,
        )

    def log_recommendation(
        self,
        request_id: str,
        user_id: str,
        num_items: int,
        pipeline: str | None,
        latency_ms: float,
    ) -> None:
        self._logger.info(
            "recommendation",
            request_id=request_id,
            user_id=user_id,
            num_items=num_items,
            pipeline=pipeline,
            latency_ms=latency_ms,
        )

    def log_error(self, request_id: str, error: str, **kwargs: Any) -> None:
        self._logger.error("error", request_id=request_id, error=error, **kwargs)
