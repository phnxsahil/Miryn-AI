import asyncio
import json
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import app.services.llm_service as llm_service
from app.api.chat import get_current_user_id
from app.main import app
from app.services.importance import score_message_llm
from app.services.llm_service import LLMService, QuotaExhausted


pytestmark = pytest.mark.live_llm


class ApiError(Exception):
    def __init__(self, message: str, code: int = 429, status: str = "RESOURCE_EXHAUSTED"):
        super().__init__(message)
        self.code = code
        self.status = status


class FakeModels:
    def __init__(self, errors=None, texts=None):
        self.errors = errors or {}
        self.texts = texts or {}
        self.calls: list[str] = []

    async def generate_content(self, *, model, contents, config):
        self.calls.append(model)
        if model in self.errors:
            raise self.errors[model]
        return SimpleNamespace(text=self.texts.get(model, "ok"))

    def generate_content_stream(self, *, model, contents, config):
        self.calls.append(model)
        if model in self.errors:
            raise self.errors[model]
        return self._stream(self.texts.get(model, "ok"))

    @staticmethod
    async def _stream(text):
        yield SimpleNamespace(text=text, candidates=[])


def _service(models, chain):
    service = LLMService.__new__(LLMService)
    service.provider = "gemini"
    service.logger = logging.getLogger("test_llm_quota")
    service.model = chain[0]
    service.gemini_fallback_models = chain
    service.client = SimpleNamespace(aio=SimpleNamespace(models=models))
    service._build_system_prompt = lambda identity: "system"
    service._format_context = lambda context: "context"
    service._build_user_prompt = lambda context, message: message
    return service


@pytest.fixture(autouse=True)
def reset_quota_state():
    with llm_service._quota_lock:
        llm_service._quota_dead_until = 0.0
        llm_service._model_quota_dead_until.clear()
    yield
    with llm_service._quota_lock:
        llm_service._quota_dead_until = 0.0
        llm_service._model_quota_dead_until.clear()


def test_all_quota_models_trip_breaker_and_second_call_is_local():
    models = FakeModels(errors={"primary": ApiError("quota retry in 12.3s"), "secondary": ApiError("RESOURCE_EXHAUSTED")})
    service = _service(models, ["primary", "secondary"])

    with pytest.raises(QuotaExhausted):
        asyncio.run(service.generate("hello"))
    assert models.calls == ["primary", "secondary"]

    with pytest.raises(QuotaExhausted):
        asyncio.run(service.generate("hello again"))
    assert models.calls == ["primary", "secondary"]


def test_per_model_quota_skip_starts_later_call_at_successful_model():
    models = FakeModels(
        errors={"primary": ApiError("429 quota")},
        texts={"secondary": "from secondary"},
    )
    service = _service(models, ["primary", "secondary"])

    assert asyncio.run(service.generate("hello")) == "from secondary"
    assert asyncio.run(service.generate("again")) == "from secondary"
    assert models.calls == ["primary", "secondary", "secondary"]


def test_breaker_and_model_skip_clear_after_cooldown(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(llm_service.time, "monotonic", lambda: now[0])
    models = FakeModels(errors={"primary": ApiError("429 quota retry in 10s")})
    service = _service(models, ["primary"])

    with pytest.raises(QuotaExhausted):
        asyncio.run(service.generate("hello"))
    assert LLMService.quota_dead()
    now[0] = 110.1
    assert not LLMService.quota_dead()
    models.errors.clear()
    assert asyncio.run(service.generate("recovered")) == "ok"
    assert models.calls == ["primary", "primary"]


def test_stream_all_quota_models_raise_quota_exhausted():
    models = FakeModels(errors={"primary": ApiError("RESOURCE_EXHAUSTED", 429), "secondary": ApiError("429 quota")})
    service = _service(models, ["primary", "secondary"])

    async def collect():
        return [chunk async for chunk in service.stream_chat({}, "hello", {})]

    with pytest.raises(QuotaExhausted):
        asyncio.run(collect())
    assert models.calls == ["primary", "secondary"]


def test_score_message_llm_skips_during_quota_cooldown():
    llm_service._mark_global_quota_dead(60)
    fake_llm = SimpleNamespace(generate=AsyncMock())

    assert asyncio.run(score_message_llm(fake_llm, "I am vegetarian")) == []
    fake_llm.generate.assert_not_awaited()


def test_chat_stream_turns_quota_failure_into_assistant_busy_reply():
    client = TestClient(app)
    user_id = "00000000-0000-0000-0000-000000000000"
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    try:
        async def quota_stream(*args, **kwargs):
            raise QuotaExhausted("quota")
            yield "never"

        redis = MagicMock()
        redis.incr.return_value = 1
        database = MagicMock()
        database.table().insert().execute.return_value = SimpleNamespace(data=[{"id": "conv-quota"}])
        database.table().update().eq().execute.return_value = SimpleNamespace(data=[])
        store = AsyncMock()
        with patch("app.api.chat.redis_client", redis), \
             patch("app.api.chat.has_sql", return_value=False), \
             patch("app.api.chat.get_db", return_value=database), \
             patch("app.api.chat.FactStore") as fact_store, \
             patch("app.api.chat.orchestrator.identity.get_identity", return_value={}), \
             patch("app.api.chat.orchestrator.memory.retrieve_context", new=AsyncMock(return_value=[])), \
             patch("app.api.chat.orchestrator.memory.store_conversation", new=store), \
             patch("app.api.chat.orchestrator.llm.stream_chat", new=quota_stream), \
             patch("app.api.chat.analyze_reflection.delay"):
            fact_store.return_value.list_top.return_value = []
            response = client.post("/chat/stream", json={"message": "hello"})

        payloads = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
        assert response.status_code == 200
        assert any(payload.get("chunk") == "I'm a bit busy right now - give me a minute and try again." for payload in payloads)
        assert payloads[-1].get("done") is True
        assert all("error" not in payload for payload in payloads)
        assert all(call.kwargs.get("role") == "user" for call in store.await_args_list)
        assert all("busy right now" not in str(call.kwargs.get("content")) for call in store.await_args_list)
    finally:
        app.dependency_overrides.clear()
