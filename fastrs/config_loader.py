"""YAML configuration loader for FastRS."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from fastrs.config import FastRSConfig

# ---------------------------------------------------------------------------
# Built-in class short-name registry
# ---------------------------------------------------------------------------

BUILTIN_CLASSES: dict[str, str] = {
    # Recall
    "PopularityRecall": "fastrs.recall.popular.PopularityRecall",
    "RandomRecall": "fastrs.recall.popular.RandomRecall",
    # Ranking
    "PassThroughRanker": "fastrs.ranking.score.PassThroughRanker",
    "WeightedFieldRanker": "fastrs.ranking.score.WeightedFieldRanker",
    # Filter
    "ExcludeItemsFilter": "fastrs.filter.rules.ExcludeItemsFilter",
    "MinScoreFilter": "fastrs.filter.rules.MinScoreFilter",
    # Pipeline
    "JSONFileLoader": "fastrs.pipeline.loader.JSONFileLoader",
    "InMemoryLoader": "fastrs.pipeline.loader.InMemoryLoader",
    "FieldSelector": "fastrs.pipeline.transform.FieldSelector",
    "DefaultValueFiller": "fastrs.pipeline.transform.DefaultValueFiller",
}


def resolve_class(class_ref: str) -> type:
    """Resolve a class short name or dotted import path to a Python class.

    Examples::

        resolve_class("PopularityRecall")
        resolve_class("fastrs.recall.popular.PopularityRecall")
        resolve_class("mypackage.custom.MyRecall")
    """
    dotted = BUILTIN_CLASSES.get(class_ref, class_ref)
    module_path, _, class_name = dotted.rpartition(".")
    if not module_path:
        raise ImportError(f"Cannot resolve class '{class_ref}': not a built-in name and not a dotted path")
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name, None)
    if cls is None:
        raise ImportError(f"Class '{class_name}' not found in module '{module_path}'")
    return cls


# ---------------------------------------------------------------------------
# YAML loading & mapping
# ---------------------------------------------------------------------------


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    """Read and parse a YAML configuration file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Config file not found: {p}")
    with open(p) as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping at top level, got {type(data).__name__}")
    return data


def yaml_to_fastrs_config(yaml_data: dict[str, Any]) -> FastRSConfig:
    """Flatten nested YAML sections into ``FastRSConfig`` keyword arguments."""
    kwargs: dict[str, Any] = {}

    # server section → direct fields
    for key in ("host", "port", "workers", "reload", "debug"):
        _extract(yaml_data, "server", key, kwargs, key)

    # engine section → add default_ prefix
    for key in ("recall_top_k", "rank_top_k", "result_top_k"):
        _extract(yaml_data, "engine", key, kwargs, f"default_{key}")

    # logging section
    _extract(yaml_data, "logging", "level", kwargs, "log_level")
    _extract(yaml_data, "logging", "format", kwargs, "log_format")
    _extract(yaml_data, "logging", "file", kwargs, "log_file")

    # storage section
    _extract(yaml_data, "storage", "model_dir", kwargs, "model_dir")

    # database section → direct fields
    for key in ("postgres_dsn", "postgres_pool_size", "postgres_max_overflow", "postgres_echo"):
        _extract(yaml_data, "database", key, kwargs, key)

    # redis section
    _extract(yaml_data, "redis", "url", kwargs, "redis_url")
    _extract(yaml_data, "redis", "max_connections", kwargs, "redis_max_connections")

    # message_queue section
    _extract(yaml_data, "message_queue", "backend", kwargs, "mq_backend")
    _extract(yaml_data, "message_queue", "redis_group", kwargs, "mq_redis_group")
    _extract(yaml_data, "message_queue", "redis_consumer", kwargs, "mq_redis_consumer")

    return FastRSConfig(**kwargs)


def _extract(data: dict, section: str, key: str, target: dict, target_key: str) -> None:
    """Copy ``data[section][key]`` into ``target[target_key]`` if present."""
    sec = data.get(section)
    if isinstance(sec, dict) and key in sec:
        target[target_key] = sec[key]


# ---------------------------------------------------------------------------
# Pydantic models for module / pipeline / model definitions in YAML
# ---------------------------------------------------------------------------


class ModuleDefinition(BaseModel):
    """Schema for a module entry in the YAML ``modules`` section."""

    model_config = {"populate_by_name": True}

    name: str
    class_ref: str = Field(alias="class")
    params: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    description: str = ""


class PipelineStageDefinition(BaseModel):
    """Schema for a pipeline stage entry in the YAML ``pipeline`` section."""

    model_config = {"populate_by_name": True}

    name: str
    class_ref: str = Field(alias="class")
    params: dict[str, Any] = Field(default_factory=dict)
    description: str = ""


class ModelDefinition(BaseModel):
    """Schema for a model entry in the YAML ``models`` section."""

    model_config = {"populate_by_name": True}

    name: str
    class_ref: str = Field(alias="class")
    version: str = "0.0.1"
    path: str = ""
    params: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Template generation
# ---------------------------------------------------------------------------

DEFAULT_TEMPLATE = """\
# =============================================================================
# FastRS Configuration
# =============================================================================
# All values below can be overridden by environment variables with the FASTRS_
# prefix.  For example, FASTRS_PORT=9000 overrides the port setting.

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
server:
  host: "0.0.0.0"
  port: 8000
  workers: 1
  reload: false
  debug: false

# ---------------------------------------------------------------------------
# Recommendation Engine
# ---------------------------------------------------------------------------
engine:
  recall_top_k: 200        # Number of candidates from recall stage
  rank_top_k: 50            # Number of items kept after ranking
  result_top_k: 10          # Final number of results returned

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging:
  level: "INFO"             # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "json"            # "json" or "console"
  file: ""                  # Log file path. Leave empty for stdout only.

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
storage:
  model_dir: "models_store"

# ---------------------------------------------------------------------------
# Database (PostgreSQL) — leave postgres_dsn empty to disable
# ---------------------------------------------------------------------------
database:
  postgres_dsn: ""          # e.g. "postgresql+asyncpg://user:pass@localhost/fastrs"
  postgres_pool_size: 10
  postgres_max_overflow: 20
  postgres_echo: false

# ---------------------------------------------------------------------------
# Redis — leave url empty to disable
# ---------------------------------------------------------------------------
redis:
  url: ""                   # e.g. "redis://localhost:6379/0"
  max_connections: 20

# ---------------------------------------------------------------------------
# Message Queue
# ---------------------------------------------------------------------------
message_queue:
  backend: "auto"           # "auto" (Redis if available, else in-memory), "redis", "memory"
  redis_group: "fastrs"     # Consumer group name (Redis Streams only)
  redis_consumer: "worker-0"

# ---------------------------------------------------------------------------
# Modules — define which recall, ranking, and filter modules to load.
#
# Each entry:
#   name:        Registry key used to reference the module
#   class:       Built-in short name (e.g. "PopularityRecall") or full dotted
#                path (e.g. "mypackage.recall.MyCustomRecall")
#   params:      Keyword arguments passed to the constructor (optional)
#   enabled:     Whether the module starts enabled (default: true)
#   description: Human-readable description (optional)
#
# Built-in classes:
#   Recall:   PopularityRecall, RandomRecall
#   Ranking:  PassThroughRanker, WeightedFieldRanker
#   Filter:   ExcludeItemsFilter, MinScoreFilter
# ---------------------------------------------------------------------------
modules:
  recall:
    - name: "popularity"
      class: "PopularityRecall"
      description: "Popularity-based recall"
      # params:
      #   item_scores:
      #     item_1: 0.95
      #     item_2: 0.80

    # - name: "random"
    #   class: "RandomRecall"
    #   params:
    #     seed: 42
    #   description: "Random recall for exploration"

  ranking:
    - name: "passthrough"
      class: "PassThroughRanker"
      description: "Pass-through ranker (score sort only)"

    # - name: "weighted"
    #   class: "WeightedFieldRanker"
    #   params:
    #     weights:
    #       rating: 0.7
    #       popularity: 0.3
    #   description: "Weighted field ranker"

  filter:
    - name: "exclude_items"
      class: "ExcludeItemsFilter"
      description: "Exclude items filter"

    # - name: "min_score"
    #   class: "MinScoreFilter"
    #   params:
    #     min_score: 0.1
    #   description: "Remove items below score threshold"

# ---------------------------------------------------------------------------
# Pipeline — data loading and transformation stages (run sequentially).
#
# Built-in classes:
#   JSONFileLoader, InMemoryLoader, FieldSelector, DefaultValueFiller
# ---------------------------------------------------------------------------
pipeline: []
  # - name: "json_loader"
  #   class: "JSONFileLoader"
  #   params:
  #     file_path: "data/items.json"
  #   description: "Load items from JSON file"

  # - name: "field_selector"
  #   class: "FieldSelector"
  #   params:
  #     fields: ["item_id", "title", "rating"]

  # - name: "default_filler"
  #   class: "DefaultValueFiller"
  #   params:
  #     defaults:
  #       rating: 0.0
  #       category: "unknown"

# ---------------------------------------------------------------------------
# Models — pre-load ML models on startup.
#
# Each entry:
#   name:    Registry key
#   class:   Full dotted path to a BaseModel subclass
#   version: Model version string
#   path:    Path to saved weights (optional)
#   params:  Constructor kwargs (optional)
# ---------------------------------------------------------------------------
models: []
  # - name: "my_model"
  #   class: "mypackage.models.MyModel"
  #   version: "1.0.0"
  #   path: "models_store/my_model_v1.pt"
  #   params: {}
"""


def generate_template(output: Path) -> None:
    """Write the default YAML configuration template to *output*."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(DEFAULT_TEMPLATE, encoding="utf-8")
