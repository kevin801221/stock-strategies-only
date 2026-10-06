import pytest
import threading
from fastapi.testclient import TestClient

from api.main import app
from stock_strategies import loader
from api.services.runs import RunManager


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STRATEGY_DIR", tmp_path)
    return TestClient(app)


def test_strategy_crud_and_invalid_payload(client):
    response = client.post("/api/strategies", json={"name": "test", "params": {"hold_days": 5}})
    assert response.status_code == 200
    sid = response.json()["id"]
    assert client.get(f"/api/strategies/{sid}").json()["params"]["hold_days"] == 5
    assert client.post("/api/strategies", json={"id": "../bad", "name": "bad"}).status_code == 400
    assert client.post("/api/strategies", json={"name": "bad", "params": {"stop_loss": 0}}).status_code == 400
    assert client.delete(f"/api/strategies/{sid}").status_code == 200
    assert client.get(f"/api/strategies/{sid}").status_code == 404


@pytest.mark.parametrize("limit", [0, -1, 1.5])
def test_invalid_run_limits_are_rejected(client, limit):
    assert client.post("/api/run", json={"strategy_id": "default", "limit": limit}).status_code == 422
    assert client.post("/api/runs", json={"strategy_id": "default", "limit": limit}).status_code == 422


def test_job_missing_strategy_and_missing_job(client):
    assert client.post("/api/runs", json={"strategy_id": "missing"}).status_code == 404
    assert client.get("/api/runs/missing").status_code == 404
    assert client.delete("/api/runs/missing").status_code == 404


def test_empty_ai_prompt_is_rejected(client):
    assert client.post("/api/strategies/generate", json={"prompt": "   "}).status_code == 422


def test_job_http_lifecycle_and_shared_admission_control(client, monkeypatch):
    import api.main as module
    entered, release = threading.Event(), threading.Event()
    def runner(strategy, limit, *, progress, cancel):
        progress(completed=0, total=2, current="2330")
        entered.set()
        assert release.wait(5)
        return {"summary": {"total": 0}}
    store = RunManager(runner=runner)
    monkeypatch.setattr(module, "runs", store)
    client.post("/api/strategies", json={"id": "test", "name": "test"})
    try:
        response = client.post("/api/runs", json={"strategy_id": "test"})
        assert response.status_code == 202
        job_id = response.json()["id"]
        assert entered.wait(5)
        assert client.get(f"/api/runs/{job_id}").json()["total"] == 2
        for path in ("/api/run", "/api/runs"):
            assert client.post(path, json={"strategy_id": "test"}).status_code == 409
        assert client.delete(f"/api/runs/{job_id}").json()["status"] == "cancelling"
    finally:
        release.set()
        store.shutdown()
    finished = client.get(f"/api/runs/{job_id}").json()
    assert finished["status"] == "cancelled"
    assert finished["result"]["summary"]["total"] == 0
