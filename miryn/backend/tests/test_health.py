from fastapi.testclient import TestClient
import pytest
from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health_check(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("status") in {"healthy", "degraded"}
    assert isinstance(payload.get("checks"), dict)
    assert "db" in payload["checks"]
    assert "redis" in payload["checks"]
    assert payload.get("version") == "0.1.0"


def test_root(client: TestClient):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json().get("message")
