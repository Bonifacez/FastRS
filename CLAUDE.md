# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is FastRS

FastRS is a production-grade recommendation system framework built with FastAPI. "RS" = Recommendation System, not Rust. Pure Python, no native extensions.

## Commands

```bash
# Install for development
pip install -e ".[dev]"

# Run tests
pytest

# Run a single test file
pytest tests/test_engine.py

# Run a single test
pytest tests/test_engine.py::test_recommend_basic -v

# Lint and format
ruff check .
ruff format .

# Start server
fastrs serve
fastrs serve --host 0.0.0.0 --port 8000 --workers 4
```

## Architecture

### Recommendation Pipeline

The core flow is **Recall → Ranking → Filter**, orchestrated by `RecommendationEngine` (`fastrs/core/engine.py`):

1. **Recall** (`fastrs/recall/`) — candidate generation (e.g., `PopularityRecall`, `RandomRecall`). ABC: `BaseRecall.recall()`
2. **Ranking** (`fastrs/ranking/`) — score and reorder candidates (e.g., `PassThroughRanker`, `WeightedFieldRanker`). ABC: `BaseRanker.rank()`
3. **Filter** (`fastrs/filter/`) — post-ranking filtering (e.g., `ExcludeItemsFilter`, `MinScoreFilter`). ABC: `BaseFilter.apply()`

### Hot-Pluggable Module System

`ModuleRegistry` (`fastrs/core/registry.py`) provides thread-safe runtime module management. Modules can be registered, enabled, disabled, restarted, and removed without server restart. Module types: RECALL, RANKING, FILTER, PIPELINE.

### Application Lifecycle

`create_app()` in `fastrs/app.py` is the FastAPI factory. The `lifespan` async context manager handles startup/teardown of PostgreSQL, Redis, message queue, and default module registration.

### Key Layers

- **API** (`fastrs/api/routes/`) — health, recommend, modules CRUD, pipeline, model management
- **Models** (`fastrs/models/`) — ML model registry with `BaseModel` ABC and optional `TorchModel` (requires `torch` extra)
- **Pipeline** (`fastrs/pipeline/`) — data loading/transformation stages (`JSONFileLoader`, `FieldSelector`, `DefaultValueFiller`)
- **Message Queue** (`fastrs/mq/`) — `InMemoryMessageQueue` (default) or `RedisStreamMessageQueue` (when Redis is configured)
- **DB** (`fastrs/db/`) — async PostgreSQL via SQLAlchemy+asyncpg, async Redis with cache helpers. Both are optional.
- **CLI** (`fastrs/cli/main.py`) — Typer-based CLI: `serve`, `version`, `health`, `module`, `model`, `pipeline` subcommands

### Configuration

All settings use `FASTRS_` env var prefix, managed via Pydantic Settings in `fastrs/config.py`. Key defaults: `DEFAULT_RECALL_TOP_K=200`, `DEFAULT_RANK_TOP_K=50`, `DEFAULT_RESULT_TOP_K=10`. PostgreSQL and Redis are opt-in via `FASTRS_POSTGRES_DSN` and `FASTRS_REDIS_URL`.

### Pydantic Models

All request/response types and enums live in `fastrs/core/types.py`: `ItemScore`, `RecommendRequest`, `RecommendResponse`, `ModuleInfo`, `ModelInfo`, `ModuleType`.

## Code Style

- Ruff with `py310` target, 120-char line length
- Lint rules: E, F, I, N, W
- Async-first: database and Redis operations are all async
- `structlog` for all logging (JSON or console format)
- `pytest-asyncio` with `asyncio_mode = "auto"` — async test functions work without `@pytest.mark.asyncio`

## Extending

To add a new recall/ranking/filter module: subclass the ABC in the corresponding package, implement the required method (`recall`/`rank`/`apply`), and register it via `ModuleRegistry` or the modules API endpoint.
