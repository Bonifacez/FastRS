from __future__ import annotations

import sys
from typing import Optional

import typer
import httpx

app = typer.Typer(
    name="fastrs",
    help="FastRS - Fast Recommendation System CLI",
    add_completion=False,
)

pipeline_app = typer.Typer(help="Manage pipelines")
model_app = typer.Typer(help="Manage models")
app.add_typer(pipeline_app, name="pipeline")
app.add_typer(model_app, name="model")


def _get_base_url(host: str, port: int) -> str:
    return f"http://{host}:{port}"


def _print_json(data: dict | list) -> None:
    import json
    typer.echo(json.dumps(data, indent=2))


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    workers: int = typer.Option(1, help="Number of workers"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
    log_level: str = typer.Option("info", help="Log level"),
) -> None:
    """Start the FastRS server."""
    import uvicorn

    typer.echo(f"Starting FastRS server on {host}:{port} with {workers} worker(s)")
    uvicorn.run(
        "fastrs.main:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
        log_level=log_level.lower(),
    )


@app.command()
def health(
    host: str = typer.Option("localhost", help="Server host"),
    port: int = typer.Option(8000, help="Server port"),
) -> None:
    """Check server health."""
    base = _get_base_url(host, port)
    try:
        resp = httpx.get(f"{base}/health/ready", timeout=5)
        _print_json(resp.json())
        if resp.json().get("status") != "ready":
            raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo(f"Cannot connect to FastRS at {base}", err=True)
        raise typer.Exit(1)


@app.command()
def config_show() -> None:
    """Show current configuration."""
    from fastrs.config import get_settings
    settings = get_settings()
    _print_json(settings.model_dump(mode="json"))


# Pipeline subcommands

@pipeline_app.command("list")
def pipeline_list(
    host: str = typer.Option("localhost", help="Server host"),
    port: int = typer.Option(8000, help="Server port"),
) -> None:
    """List all pipelines."""
    base = _get_base_url(host, port)
    try:
        resp = httpx.get(f"{base}/pipelines", timeout=5)
        resp.raise_for_status()
        _print_json(resp.json())
    except httpx.ConnectError:
        typer.echo("Cannot connect to FastRS server", err=True)
        raise typer.Exit(1)


@pipeline_app.command("add")
def pipeline_add(
    name: str = typer.Argument(..., help="Pipeline name"),
    recall: Optional[str] = typer.Option(None, help="Recall module name"),
    ranking: Optional[str] = typer.Option(None, help="Ranking module name"),
    filters: Optional[str] = typer.Option(None, help="Comma-separated filter names"),
    host: str = typer.Option("localhost", help="Server host"),
    port: int = typer.Option(8000, help="Server port"),
) -> None:
    """Add a new pipeline."""
    base = _get_base_url(host, port)
    payload: dict = {"name": name}
    if recall:
        payload["recall_module"] = recall
    if ranking:
        payload["ranking_module"] = ranking
    if filters:
        payload["filter_modules"] = [f.strip() for f in filters.split(",")]
    try:
        resp = httpx.post(f"{base}/pipelines", json=payload, timeout=5)
        resp.raise_for_status()
        _print_json(resp.json())
    except httpx.HTTPStatusError as e:
        typer.echo(f"Error: {e.response.text}", err=True)
        raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo("Cannot connect to FastRS server", err=True)
        raise typer.Exit(1)


@pipeline_app.command("remove")
def pipeline_remove(
    name: str = typer.Argument(..., help="Pipeline name"),
    host: str = typer.Option("localhost", help="Server host"),
    port: int = typer.Option(8000, help="Server port"),
) -> None:
    """Remove a pipeline."""
    base = _get_base_url(host, port)
    try:
        resp = httpx.delete(f"{base}/pipelines/{name}", timeout=5)
        resp.raise_for_status()
        _print_json(resp.json())
    except httpx.HTTPStatusError as e:
        typer.echo(f"Error: {e.response.text}", err=True)
        raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo("Cannot connect to FastRS server", err=True)
        raise typer.Exit(1)


@pipeline_app.command("restart")
def pipeline_restart(
    name: str = typer.Argument(..., help="Pipeline name"),
    host: str = typer.Option("localhost", help="Server host"),
    port: int = typer.Option(8000, help="Server port"),
) -> None:
    """Restart a pipeline."""
    base = _get_base_url(host, port)
    try:
        resp = httpx.post(f"{base}/pipelines/{name}/restart", timeout=5)
        resp.raise_for_status()
        _print_json(resp.json())
    except httpx.HTTPStatusError as e:
        typer.echo(f"Error: {e.response.text}", err=True)
        raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo("Cannot connect to FastRS server", err=True)
        raise typer.Exit(1)


# Model subcommands

@model_app.command("list")
def model_list(
    host: str = typer.Option("localhost", help="Server host"),
    port: int = typer.Option(8000, help="Server port"),
) -> None:
    """List all loaded models."""
    base = _get_base_url(host, port)
    try:
        resp = httpx.get(f"{base}/models", timeout=5)
        resp.raise_for_status()
        _print_json(resp.json())
    except httpx.ConnectError:
        typer.echo("Cannot connect to FastRS server", err=True)
        raise typer.Exit(1)


@model_app.command("train")
def model_train(
    model_name: str = typer.Argument(..., help="Model name"),
    epochs: int = typer.Option(10, help="Training epochs"),
    lr: float = typer.Option(0.001, help="Learning rate"),
    batch_size: int = typer.Option(32, help="Batch size"),
    host: str = typer.Option("localhost", help="Server host"),
    port: int = typer.Option(8000, help="Server port"),
) -> None:
    """Trigger model training on the server."""
    base = _get_base_url(host, port)
    payload = {
        "model_name": model_name,
        "epochs": epochs,
        "learning_rate": lr,
        "batch_size": batch_size,
    }
    try:
        resp = httpx.post(f"{base}/models/train", json=payload, timeout=10)
        resp.raise_for_status()
        _print_json(resp.json())
    except httpx.HTTPStatusError as e:
        typer.echo(f"Error: {e.response.text}", err=True)
        raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo("Cannot connect to FastRS server", err=True)
        raise typer.Exit(1)


@model_app.command("load")
def model_load(
    model_name: str = typer.Argument(..., help="Model name"),
    model_path: str = typer.Argument(..., help="Path to model directory"),
    host: str = typer.Option("localhost", help="Server host"),
    port: int = typer.Option(8000, help="Server port"),
) -> None:
    """Load a model on the server."""
    base = _get_base_url(host, port)
    payload = {"model_name": model_name, "model_path": model_path}
    try:
        resp = httpx.post(f"{base}/models/load", json=payload, timeout=10)
        resp.raise_for_status()
        _print_json(resp.json())
    except httpx.HTTPStatusError as e:
        typer.echo(f"Error: {e.response.text}", err=True)
        raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo("Cannot connect to FastRS server", err=True)
        raise typer.Exit(1)


@model_app.command("remove")
def model_remove(
    model_name: str = typer.Argument(..., help="Model name"),
    host: str = typer.Option("localhost", help="Server host"),
    port: int = typer.Option(8000, help="Server port"),
) -> None:
    """Unload a model from the server."""
    base = _get_base_url(host, port)
    try:
        resp = httpx.delete(f"{base}/models/{model_name}", timeout=5)
        resp.raise_for_status()
        _print_json(resp.json())
    except httpx.HTTPStatusError as e:
        typer.echo(f"Error: {e.response.text}", err=True)
        raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo("Cannot connect to FastRS server", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
