"""FastRS CLI — manage the recommendation system from the command line."""

from __future__ import annotations

from typing import Optional

import typer

from fastrs import __version__

app = typer.Typer(
    name="fastrs",
    help="FastRS — A production-grade Recommendation System for Everything",
    add_completion=True,
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# Top-level commands
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """Print the FastRS version."""
    typer.echo(f"FastRS v{__version__}")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    workers: int = typer.Option(1, help="Number of uvicorn workers"),
    reload: bool = typer.Option(False, help="Enable auto-reload (dev mode)"),
    log_level: str = typer.Option("info", help="Log level"),
) -> None:
    """Start the FastRS API server."""
    import uvicorn

    typer.echo(f"🚀 Starting FastRS v{__version__} on {host}:{port}")
    uvicorn.run(
        "fastrs.app:create_app",
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        log_level=log_level.lower(),
        factory=True,
    )


# ---------------------------------------------------------------------------
# Module management sub-commands
# ---------------------------------------------------------------------------

module_app = typer.Typer(name="module", help="Manage recommendation modules (hot-plug)")
app.add_typer(module_app)


@module_app.command("list")
def module_list(
    module_type: Optional[str] = typer.Option(None, help="Filter by type: recall, ranking, filter, pipeline"),
) -> None:
    """List registered modules via the API."""
    import httpx

    base = _api_base()
    params: dict[str, str] = {}
    if module_type:
        params["module_type"] = module_type
    try:
        resp = httpx.get(f"{base}/api/v1/modules/", params=params, timeout=5)
        resp.raise_for_status()
        modules = resp.json()
        if not modules:
            typer.echo("No modules registered.")
            return
        for m in modules:
            status = "✅" if m.get("enabled") else "❌"
            typer.echo(f"  {status} [{m['module_type']}] {m['name']}  — {m.get('description', '')}")
    except httpx.ConnectError:
        typer.echo("❌ Cannot connect to FastRS server. Is it running?", err=True)
        raise typer.Exit(1)


@module_app.command("enable")
def module_enable(name: str = typer.Argument(..., help="Module name")) -> None:
    """Enable a module at runtime."""
    _module_action(name, "enable")


@module_app.command("disable")
def module_disable(name: str = typer.Argument(..., help="Module name")) -> None:
    """Disable a module at runtime."""
    _module_action(name, "disable")


@module_app.command("remove")
def module_remove(name: str = typer.Argument(..., help="Module name")) -> None:
    """Unregister (remove) a module at runtime."""
    import httpx

    base = _api_base()
    try:
        resp = httpx.delete(f"{base}/api/v1/modules/{name}", timeout=5)
        if resp.status_code == 404:
            typer.echo(f"❌ Module '{name}' not found.", err=True)
            raise typer.Exit(1)
        resp.raise_for_status()
        typer.echo(f"🗑️  Module '{name}' removed.")
    except httpx.ConnectError:
        typer.echo("❌ Cannot connect to FastRS server. Is it running?", err=True)
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Model management sub-commands
# ---------------------------------------------------------------------------

model_app = typer.Typer(name="model", help="Manage ML models")
app.add_typer(model_app)


@model_app.command("list")
def model_list() -> None:
    """List managed models."""
    import httpx

    base = _api_base()
    try:
        resp = httpx.get(f"{base}/api/v1/models/", timeout=5)
        resp.raise_for_status()
        models = resp.json()
        if not models:
            typer.echo("No models registered.")
            return
        for m in models:
            typer.echo(f"  [{m['status']}] {m['name']} v{m['version']}")
    except httpx.ConnectError:
        typer.echo("❌ Cannot connect to FastRS server. Is it running?", err=True)
        raise typer.Exit(1)


@model_app.command("save")
def model_save(name: str = typer.Argument(..., help="Model name")) -> None:
    """Save model weights to disk."""
    import httpx

    base = _api_base()
    try:
        resp = httpx.post(f"{base}/api/v1/models/{name}/save", timeout=30)
        if resp.status_code == 400:
            typer.echo(f"❌ {resp.json().get('detail', 'Error')}", err=True)
            raise typer.Exit(1)
        resp.raise_for_status()
        data = resp.json()
        typer.echo(f"💾 Model '{name}' saved to {data.get('path')}")
    except httpx.ConnectError:
        typer.echo("❌ Cannot connect to FastRS server. Is it running?", err=True)
        raise typer.Exit(1)


@model_app.command("remove")
def model_remove(name: str = typer.Argument(..., help="Model name")) -> None:
    """Remove a model."""
    import httpx

    base = _api_base()
    try:
        resp = httpx.delete(f"{base}/api/v1/models/{name}", timeout=5)
        if resp.status_code == 404:
            typer.echo(f"❌ Model '{name}' not found.", err=True)
            raise typer.Exit(1)
        resp.raise_for_status()
        typer.echo(f"🗑️  Model '{name}' removed.")
    except httpx.ConnectError:
        typer.echo("❌ Cannot connect to FastRS server. Is it running?", err=True)
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Pipeline sub-commands
# ---------------------------------------------------------------------------

pipeline_app = typer.Typer(name="pipeline", help="Data pipeline operations")
app.add_typer(pipeline_app)


@pipeline_app.command("run")
def pipeline_run() -> None:
    """Trigger a data pipeline run."""
    import httpx

    base = _api_base()
    try:
        resp = httpx.post(f"{base}/api/v1/pipeline/run", timeout=60)
        if resp.status_code == 404:
            typer.echo("❌ No pipeline modules registered.", err=True)
            raise typer.Exit(1)
        resp.raise_for_status()
        typer.echo(f"✅ Pipeline complete: {resp.json()}")
    except httpx.ConnectError:
        typer.echo("❌ Cannot connect to FastRS server. Is it running?", err=True)
        raise typer.Exit(1)


@pipeline_app.command("list")
def pipeline_list() -> None:
    """List pipeline stages."""
    import httpx

    base = _api_base()
    try:
        resp = httpx.get(f"{base}/api/v1/pipeline/", timeout=5)
        resp.raise_for_status()
        stages = resp.json()
        if not stages:
            typer.echo("No pipeline stages registered.")
            return
        for s in stages:
            status = "✅" if s.get("enabled") else "❌"
            typer.echo(f"  {status} {s['name']}  — {s.get('description', '')}")
    except httpx.ConnectError:
        typer.echo("❌ Cannot connect to FastRS server. Is it running?", err=True)
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Health / Info
# ---------------------------------------------------------------------------


@app.command()
def health() -> None:
    """Check if the FastRS server is alive."""
    import httpx

    base = _api_base()
    try:
        resp = httpx.get(f"{base}/healthz", timeout=5)
        resp.raise_for_status()
        typer.echo(f"✅ Server is healthy: {resp.json()}")
    except httpx.ConnectError:
        typer.echo("❌ Cannot connect to FastRS server. Is it running?", err=True)
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SERVER_URL: str = "http://127.0.0.1:8000"


def _api_base() -> str:
    import os

    return os.environ.get("FASTRS_API_URL", _SERVER_URL)


def _module_action(name: str, action: str) -> None:
    import httpx

    base = _api_base()
    try:
        resp = httpx.post(f"{base}/api/v1/modules/{name}/{action}", timeout=5)
        if resp.status_code == 404:
            typer.echo(f"❌ Module '{name}' not found.", err=True)
            raise typer.Exit(1)
        resp.raise_for_status()
        typer.echo(f"✅ Module '{name}' {action}d.")
    except httpx.ConnectError:
        typer.echo("❌ Cannot connect to FastRS server. Is it running?", err=True)
        raise typer.Exit(1)
