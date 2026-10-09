from app.core import encryption
from app.config import settings
from contextlib import nullcontext
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.services.fact_store import FactStore
from app.services.importance import ScoredFact
import logging


def test_encrypt_decrypt_roundtrip():
    original_key = settings.ENCRYPTION_KEY
    try:
        settings.ENCRYPTION_KEY = "test_key_123"
        plain = "secret payload"
        token = encryption.encrypt_text(plain)
        assert token is not None
        decoded = encryption.decrypt_text(token)
        assert decoded == plain
    finally:
        settings.ENCRYPTION_KEY = original_key


def test_missing_key_degrades_health_and_skips_fact_write(monkeypatch, caplog):
    from app import main
    from app.services import fact_store

    monkeypatch.setattr(settings, "ENCRYPTION_KEY", None)
    monkeypatch.setattr(settings, "SENTRY_ENVIRONMENT", "test")
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setattr(main, "get_sql_session", lambda: nullcontext(SimpleNamespace(execute=lambda *args, **kwargs: None)))
    monkeypatch.setattr(main.redis_client, "ping", lambda: True)

    with caplog.at_level(logging.ERROR, logger="app.main"):
        with TestClient(main.app) as client:
            response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["checks"]["encryption"] == "missing"
    assert response.json()["status"] == "degraded"
    assert caplog.text.count("ENCRYPTION_KEY is missing or invalid") == 1

    monkeypatch.setattr(fact_store, "has_sql", lambda: True)
    monkeypatch.setattr(fact_store, "get_sql_session", lambda: (_ for _ in ()).throw(AssertionError("must skip DB write")))
    FactStore().upsert_facts("user-1", [ScoredFact("Moved to Pune", "identity", 0.9, 0.0, "heuristic")])
