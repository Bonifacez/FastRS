"""Tests for the CLI module."""

from typer.testing import CliRunner

from fastrs.cli.main import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "FastRS" in result.output


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])
    # no_args_is_help returns exit code 0 with help text
    assert "FastRS" in result.output
