from __future__ import annotations

import uvicorn

from fastrs.config import get_settings
from fastrs.core.app import create_app

app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "fastrs.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
