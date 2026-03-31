"""Tests for the configuration module."""

from fastrs.config import FastRSConfig, get_config


def test_default_config() -> None:
    cfg = FastRSConfig()
    assert cfg.host == "0.0.0.0"
    assert cfg.port == 8000
    assert cfg.default_recall_top_k == 200
    assert cfg.default_rank_top_k == 50
    assert cfg.default_result_top_k == 10
    assert cfg.log_level == "INFO"


def test_get_config() -> None:
    cfg = get_config()
    assert isinstance(cfg, FastRSConfig)
