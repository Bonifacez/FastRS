from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from fastrs.core.app import create_app


@pytest_asyncio.fixture
async def client():
    app = create_app()
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "FastRS" in data.get("name", "")


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_health_ready(client):
    resp = await client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_health_live(client):
    resp = await client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_recommend(client):
    resp = await client.post("/recommend", json={"user_id": "user_1", "top_k": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "user_1"
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 5
    for item in data["items"]:
        assert "item_id" in item
        assert "score" in item


@pytest.mark.asyncio
async def test_recommend_default_pipeline(client):
    resp = await client.post("/recommend", json={"user_id": "user_42", "top_k": 10, "pipeline": "default"})
    assert resp.status_code == 200
    assert resp.json()["pipeline"] == "default"


@pytest.mark.asyncio
async def test_recommend_collaborative_pipeline(client):
    resp = await client.post("/recommend", json={"user_id": "user_1", "top_k": 5, "pipeline": "collaborative"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_recommend_invalid_pipeline(client):
    resp = await client.post("/recommend", json={"user_id": "user_1", "pipeline": "nonexistent_xyz"})
    # Should fallback to another available pipeline or 503
    assert resp.status_code in (200, 503)


@pytest.mark.asyncio
async def test_batch_recommend(client):
    payload = {
        "requests": [
            {"user_id": "user_1", "top_k": 3},
            {"user_id": "user_2", "top_k": 3},
        ]
    }
    resp = await client.post("/recommend/batch", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["responses"]) == 2
    assert data["total_latency_ms"] is not None


@pytest.mark.asyncio
async def test_pipeline_list(client):
    resp = await client.get("/pipelines")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    names = [p["name"] for p in data]
    assert "default" in names


@pytest.mark.asyncio
async def test_pipeline_get(client):
    resp = await client.get("/pipelines/default")
    assert resp.status_code == 200
    assert resp.json()["name"] == "default"


@pytest.mark.asyncio
async def test_pipeline_get_not_found(client):
    resp = await client.get("/pipelines/nonexistent_xyz")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pipeline_create_and_delete(client):
    payload = {"name": "test_pipe_api"}
    resp = await client.post("/pipelines", json=payload)
    assert resp.status_code == 200
    assert resp.json()["name"] == "test_pipe_api"

    resp2 = await client.delete("/pipelines/test_pipe_api")
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_pipeline_restart(client):
    resp = await client.post("/pipelines/default/restart")
    assert resp.status_code == 200
    assert resp.json()["status"] == "restarted"


@pytest.mark.asyncio
async def test_model_list(client):
    resp = await client.get("/models")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_request_id_header(client):
    resp = await client.get("/health")
    assert "x-request-id" in resp.headers


@pytest.mark.asyncio
async def test_latency_header(client):
    resp = await client.get("/health")
    assert "x-latency-ms" in resp.headers
