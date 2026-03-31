"""Tests for the FastAPI application and endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from fastrs.app import _register_defaults, create_app
from fastrs.config import FastRSConfig
from fastrs.core.engine import RecommendationEngine
from fastrs.core.registry import ModuleRegistry
from fastrs.models.manager import ModelManager


@pytest.fixture()
def test_app():
    config = FastRSConfig(log_level="WARNING", log_format="console")
    app = create_app(config)
    # Initialize state directly (bypassing lifespan for test transport)
    registry = ModuleRegistry()
    _register_defaults(registry)
    app.state.registry = registry
    app.state.engine = RecommendationEngine(registry, config)
    app.state.model_manager = ModelManager(model_dir="/tmp/fastrs_test_models")
    return app


@pytest.fixture()
async def client(test_app) -> AsyncClient:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_healthz(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_readyz(client: AsyncClient) -> None:
    resp = await client.get("/readyz")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_info(client: AsyncClient) -> None:
    resp = await client.get("/info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "FastRS"
    assert "version" in data


@pytest.mark.asyncio
async def test_recommend(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/recommend", json={"user_id": "u1", "top_k": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "u1"
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_modules(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/modules/")
    assert resp.status_code == 200
    modules = resp.json()
    assert isinstance(modules, list)
    # Default modules should be registered
    names = {m["name"] for m in modules}
    assert "popularity" in names
    assert "passthrough" in names


@pytest.mark.asyncio
async def test_disable_enable_module(client: AsyncClient) -> None:
    # disable
    resp = await client.post("/api/v1/modules/popularity/disable")
    assert resp.status_code == 200

    # verify disabled
    resp = await client.get("/api/v1/modules/")
    pop = [m for m in resp.json() if m["name"] == "popularity"][0]
    assert not pop["enabled"]

    # re-enable
    resp = await client.post("/api/v1/modules/popularity/enable")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_unregister_module(client: AsyncClient) -> None:
    resp = await client.delete("/api/v1/modules/exclude_items")
    assert resp.status_code == 200

    # verify gone
    resp = await client.get("/api/v1/modules/")
    names = {m["name"] for m in resp.json()}
    assert "exclude_items" not in names


@pytest.mark.asyncio
async def test_list_models(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/models/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_module_not_found(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/modules/nonexistent/enable")
    assert resp.status_code == 404
