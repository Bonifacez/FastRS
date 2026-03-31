"""Tests for the YAML configuration loader."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from fastrs.cli.main import app
from fastrs.config import FastRSConfig, get_config
from fastrs.config_loader import (
    DEFAULT_TEMPLATE,
    ModuleDefinition,
    PipelineStageDefinition,
    generate_template,
    load_yaml_config,
    resolve_class,
    yaml_to_fastrs_config,
)
from fastrs.core.registry import ModuleRegistry
from fastrs.core.types import ModuleType

runner = CliRunner()


# ---------------------------------------------------------------------------
# Template generation
# ---------------------------------------------------------------------------


def test_generate_template(tmp_path: Path) -> None:
    out = tmp_path / "fastrs.yaml"
    generate_template(out)
    assert out.exists()
    data = yaml.safe_load(out.read_text())
    assert data["server"]["port"] == 8000
    assert data["engine"]["recall_top_k"] == 200
    assert data["logging"]["level"] == "INFO"


def test_generate_template_creates_parents(tmp_path: Path) -> None:
    out = tmp_path / "sub" / "dir" / "fastrs.yaml"
    generate_template(out)
    assert out.exists()


def test_default_template_is_valid_yaml() -> None:
    data = yaml.safe_load(DEFAULT_TEMPLATE)
    assert isinstance(data, dict)
    assert "server" in data
    assert "modules" in data


# ---------------------------------------------------------------------------
# CLI init command
# ---------------------------------------------------------------------------


def test_cli_init(tmp_path: Path) -> None:
    out = tmp_path / "test.yaml"
    result = runner.invoke(app, ["init", "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()


def test_cli_init_no_overwrite(tmp_path: Path) -> None:
    out = tmp_path / "test.yaml"
    out.write_text("existing")
    result = runner.invoke(app, ["init", "--output", str(out)])
    assert result.exit_code == 1
    assert out.read_text() == "existing"


def test_cli_init_force(tmp_path: Path) -> None:
    out = tmp_path / "test.yaml"
    out.write_text("existing")
    result = runner.invoke(app, ["init", "--output", str(out), "--force"])
    assert result.exit_code == 0
    assert "server" in out.read_text()


# ---------------------------------------------------------------------------
# YAML loading
# ---------------------------------------------------------------------------


def test_load_yaml_config(tmp_path: Path) -> None:
    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text("server:\n  port: 9000\n")
    data = load_yaml_config(cfg_file)
    assert data["server"]["port"] == 9000


def test_load_yaml_config_missing() -> None:
    with pytest.raises(FileNotFoundError):
        load_yaml_config("/nonexistent/path.yaml")


def test_load_yaml_config_invalid(tmp_path: Path) -> None:
    cfg_file = tmp_path / "bad.yaml"
    cfg_file.write_text("just a string")
    with pytest.raises(ValueError, match="mapping"):
        load_yaml_config(cfg_file)


# ---------------------------------------------------------------------------
# YAML → FastRSConfig mapping
# ---------------------------------------------------------------------------


def test_yaml_to_fastrs_config_full() -> None:
    data = {
        "server": {"host": "127.0.0.1", "port": 9000, "workers": 4},
        "engine": {"recall_top_k": 100, "rank_top_k": 20, "result_top_k": 5},
        "logging": {"level": "DEBUG", "format": "console", "file": "/tmp/fastrs.log"},
        "storage": {"model_dir": "/tmp/models"},
        "database": {"postgres_dsn": "postgresql+asyncpg://u:p@localhost/db"},
        "redis": {"url": "redis://localhost:6379/0", "max_connections": 50},
        "message_queue": {"backend": "memory", "redis_group": "grp", "redis_consumer": "c1"},
    }
    cfg = yaml_to_fastrs_config(data)
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 9000
    assert cfg.workers == 4
    assert cfg.default_recall_top_k == 100
    assert cfg.default_rank_top_k == 20
    assert cfg.default_result_top_k == 5
    assert cfg.log_level == "DEBUG"
    assert cfg.log_format == "console"
    assert cfg.log_file == "/tmp/fastrs.log"
    assert cfg.model_dir == "/tmp/models"
    assert cfg.postgres_dsn == "postgresql+asyncpg://u:p@localhost/db"
    assert cfg.redis_url == "redis://localhost:6379/0"
    assert cfg.redis_max_connections == 50
    assert cfg.mq_backend == "memory"
    assert cfg.mq_redis_group == "grp"
    assert cfg.mq_redis_consumer == "c1"


def test_yaml_to_fastrs_config_partial() -> None:
    """Partial YAML still works — missing sections use defaults."""
    data = {"server": {"port": 3000}}
    cfg = yaml_to_fastrs_config(data)
    assert cfg.port == 3000
    assert cfg.host == "0.0.0.0"  # default
    assert cfg.default_recall_top_k == 200  # default


def test_yaml_to_fastrs_config_empty() -> None:
    cfg = yaml_to_fastrs_config({})
    assert cfg.port == 8000


def test_env_overrides_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables should override YAML values."""
    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text("server:\n  port: 3000\n")
    monkeypatch.setenv("FASTRS_PORT", "9999")
    cfg = get_config(str(cfg_file))
    assert cfg.port == 9999


# ---------------------------------------------------------------------------
# Class resolution
# ---------------------------------------------------------------------------


def test_resolve_class_builtin() -> None:
    from fastrs.recall.popular import PopularityRecall

    cls = resolve_class("PopularityRecall")
    assert cls is PopularityRecall


def test_resolve_class_dotted() -> None:
    from fastrs.ranking.score import WeightedFieldRanker

    cls = resolve_class("fastrs.ranking.score.WeightedFieldRanker")
    assert cls is WeightedFieldRanker


def test_resolve_class_all_builtins() -> None:
    from fastrs.config_loader import BUILTIN_CLASSES

    for short_name in BUILTIN_CLASSES:
        cls = resolve_class(short_name)
        assert cls is not None


def test_resolve_class_unknown() -> None:
    with pytest.raises(ImportError):
        resolve_class("NoSuchClassAnywhere")


# ---------------------------------------------------------------------------
# Pydantic definition models
# ---------------------------------------------------------------------------


def test_module_definition_from_yaml() -> None:
    entry = {"name": "test", "class": "PopularityRecall", "params": {"item_scores": {"a": 1}}}
    defn = ModuleDefinition.model_validate(entry)
    assert defn.name == "test"
    assert defn.class_ref == "PopularityRecall"
    assert defn.enabled is True
    assert defn.params == {"item_scores": {"a": 1}}


def test_pipeline_definition_from_yaml() -> None:
    entry = {"name": "loader", "class": "JSONFileLoader", "params": {"file_path": "data.json"}}
    defn = PipelineStageDefinition.model_validate(entry)
    assert defn.class_ref == "JSONFileLoader"


# ---------------------------------------------------------------------------
# Config-driven module registration
# ---------------------------------------------------------------------------


def test_register_modules_from_config() -> None:
    from fastrs.app import _register_modules_from_config

    registry = ModuleRegistry()
    modules_config = {
        "recall": [
            {"name": "pop", "class": "PopularityRecall", "description": "pop recall"},
        ],
        "ranking": [
            {"name": "pt", "class": "PassThroughRanker"},
        ],
        "filter": [
            {"name": "exc", "class": "ExcludeItemsFilter", "enabled": False},
        ],
    }
    _register_modules_from_config(registry, modules_config)

    assert len(registry.list_modules()) == 3
    assert registry.get_info("pop").module_type == ModuleType.RECALL
    assert registry.get_info("pt").module_type == ModuleType.RANKING
    assert registry.get_info("exc").enabled is False


def test_register_modules_with_params() -> None:
    from fastrs.app import _register_modules_from_config

    registry = ModuleRegistry()
    modules_config = {
        "ranking": [
            {
                "name": "weighted",
                "class": "WeightedFieldRanker",
                "params": {"weights": {"rating": 0.7}},
            },
        ],
    }
    _register_modules_from_config(registry, modules_config)
    instance = registry.get("weighted")
    assert instance.weights == {"rating": 0.7}


# ---------------------------------------------------------------------------
# get_config with path
# ---------------------------------------------------------------------------


def test_get_config_with_yaml(tmp_path: Path) -> None:
    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text("server:\n  port: 4567\nlogging:\n  level: DEBUG\n")
    cfg = get_config(str(cfg_file))
    assert isinstance(cfg, FastRSConfig)
    assert cfg.port == 4567
    assert cfg.log_level == "DEBUG"


# ---------------------------------------------------------------------------
# New config fields
# ---------------------------------------------------------------------------


def test_config_new_fields() -> None:
    cfg = FastRSConfig()
    assert cfg.log_file == ""
    assert cfg.mq_backend == "auto"
    assert cfg.mq_redis_group == "fastrs"
    assert cfg.mq_redis_consumer == "worker-0"
