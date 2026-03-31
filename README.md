# FastRS

A production-grade Recommendation System for Everything, built with [FastAPI](https://fastapi.tiangolo.com/).

## Features

- **High Performance** — Async FastAPI server with uvicorn workers for high concurrency
- **Hot-Pluggable Modules** — Register, enable, disable, restart, and remove recall / ranking / filter modules at runtime
- **Full Recommendation Pipeline** — Recall → Ranking → Filtering, orchestrated by a central engine
- **Data Pipeline** — Extensible loader / transformer stages for data ingestion
- **PyTorch Integration** — Base model class, model manager for training / deploying PyTorch models
- **CLI (`fastrs`)** — Manage the server, modules, models, and pipelines from the command line
- **AI-Agent Friendly** — Structured JSON API with OpenAPI docs, typed request/response models
- **Structured Logging** — JSON-formatted logs via `structlog`

## Quick Start

### Install

```bash
pip install -e ".[dev]"
# For PyTorch support:
pip install -e ".[all]"
```

### Start the server

```bash
fastrs serve
# or with options:
fastrs serve --host 0.0.0.0 --port 8000 --workers 4
```

### CLI commands

```bash
fastrs --help            # Show all commands
fastrs version           # Print version
fastrs serve             # Start the API server
fastrs health            # Check server health

# Module management (hot-plug)
fastrs module list                  # List registered modules
fastrs module enable <name>        # Enable a module
fastrs module disable <name>       # Disable a module
fastrs module remove <name>        # Remove a module

# Model management
fastrs model list                   # List managed models
fastrs model save <name>           # Save model to disk
fastrs model remove <name>         # Remove a model

# Pipeline
fastrs pipeline list               # List pipeline stages
fastrs pipeline run                # Run the data pipeline
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/healthz` | Liveness probe |
| `GET` | `/readyz` | Readiness probe |
| `GET` | `/info` | Service version info |
| `POST` | `/api/v1/recommend` | Generate recommendations |
| `GET` | `/api/v1/modules/` | List modules |
| `POST` | `/api/v1/modules/{name}/enable` | Enable a module |
| `POST` | `/api/v1/modules/{name}/disable` | Disable a module |
| `DELETE` | `/api/v1/modules/{name}` | Remove a module |
| `GET` | `/api/v1/models/` | List models |
| `POST` | `/api/v1/models/{name}/save` | Save model weights |
| `DELETE` | `/api/v1/models/{name}` | Remove a model |
| `GET` | `/api/v1/pipeline/` | List pipeline stages |
| `POST` | `/api/v1/pipeline/run` | Trigger pipeline |

Interactive docs at `http://localhost:8000/docs` (Swagger UI) after starting the server.

## Project Structure

```
fastrs/
├── app.py               # FastAPI application factory
├── config.py             # Configuration (env vars with FASTRS_ prefix)
├── log.py                # Structured logging setup
├── cli/                  # Typer CLI
├── api/
│   ├── routes/           # API route handlers
│   └── middleware.py     # Request logging middleware
├── core/
│   ├── engine.py         # Recommendation engine (recall→rank→filter)
│   ├── registry.py       # Hot-pluggable module registry
│   └── types.py          # Pydantic models & type definitions
├── db/
│   ├── postgres.py       # Async PostgreSQL (SQLAlchemy + asyncpg)
│   └── redis.py          # Async Redis cache client
├── mq/
│   ├── base.py           # Abstract message queue interface
│   ├── memory.py         # In-memory async queue (default)
│   └── redis_stream.py   # Redis Streams queue (persistent)
├── pipeline/             # Data pipeline (loaders, transformers)
├── recall/               # Recall strategies (popularity, random)
├── ranking/              # Ranking strategies (passthrough, weighted)
├── filter/               # Post-ranking filters (exclude, min-score)
├── models/               # ML model management (PyTorch base)
└── utils/                # Helpers
```

## Configuration

All settings can be overridden via environment variables with the `FASTRS_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `FASTRS_HOST` | `0.0.0.0` | Server bind host |
| `FASTRS_PORT` | `8000` | Server bind port |
| `FASTRS_WORKERS` | `1` | Uvicorn workers |
| `FASTRS_LOG_LEVEL` | `INFO` | Log level |
| `FASTRS_LOG_FORMAT` | `json` | Log format (`json` or `console`) |
| `FASTRS_DEFAULT_RECALL_TOP_K` | `200` | Recall candidates count |
| `FASTRS_DEFAULT_RANK_TOP_K` | `50` | Ranked items count |
| `FASTRS_DEFAULT_RESULT_TOP_K` | `10` | Final results count |
| `FASTRS_MODEL_DIR` | `models_store` | Model storage directory |
| `FASTRS_POSTGRES_DSN` | _(empty)_ | PostgreSQL DSN (e.g. `postgresql+asyncpg://user:pass@host/db`) |
| `FASTRS_POSTGRES_POOL_SIZE` | `10` | PG connection pool size |
| `FASTRS_REDIS_URL` | _(empty)_ | Redis URL (e.g. `redis://localhost:6379/0`) |
| `FASTRS_REDIS_MAX_CONNECTIONS` | `20` | Redis pool max connections |

## PostgreSQL & Redis

Both services are **optional** — the server starts without them when DSN/URL are empty.

```bash
# Enable PostgreSQL
export FASTRS_POSTGRES_DSN="postgresql+asyncpg://user:pass@localhost:5432/fastrs"

# Enable Redis (cache + Redis Streams message queue)
export FASTRS_REDIS_URL="redis://localhost:6379/0"

fastrs serve
```

The `/readyz` endpoint reports the health of connected services:
```json
{"status": "ready", "postgres": "ok", "redis": "ok"}
```

## Message Queue

FastRS ships with two MQ backends:

| Backend | When used | Persistence | Dependencies |
|---------|-----------|-------------|--------------|
| `InMemoryMessageQueue` | `FASTRS_REDIS_URL` is empty (default) | In-process only | None |
| `RedisStreamMessageQueue` | `FASTRS_REDIS_URL` is set | Yes (Redis Streams) | `redis` |

The Redis Streams backend uses consumer groups (`XREADGROUP`) with acknowledgement
(`XACK`), giving at-least-once delivery. Unlike Redis Pub/Sub, messages are **not lost**
when no consumer is listening.

## License

MIT
