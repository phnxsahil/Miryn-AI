import asyncio
import logging
from types import SimpleNamespace

import pytest

import app.services.llm_service as llm_service
from app.services.llm_service import LLMService, QuotaExhausted
from app.workers.outreach_worker import _provider_side_failure


pytestmark = pytest.mark.live_llm


class ApiError(Exception):
    def __init__(self, message: str, code: int | None = None, status: str | None = None):
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


def _service(models, chain):
    service = LLMService.__new__(LLMService)
    service.provider = "gemini"
    service.logger = logging.getLogger("test_llm_error_classification")
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


# --- sanitised classification ---

def test_error_class_known_shapes_without_message_leakage():
    secret = "sensitive prompt fragment xyzzy"
    assert llm_service._gemini_error_class(ApiError(secret, 429, "RESOURCE_EXHAUSTED")) == "quota"
    assert llm_service._gemini_error_class(ApiError(secret, 404, "NOT_FOUND")) == "not_found"
    assert llm_service._gemini_error_class(ApiError(secret, 503, "UNAVAILABLE")) == "http_503"
    assert llm_service._gemini_error_class(ApiError(secret, None, "DEADLINE_EXCEEDED")) == "status_deadline_exceeded"
    assert llm_service._gemini_error_class(ValueError(secret)) == "ValueError"
    for exc in (ApiError(secret, 404, "NOT_FOUND"), ValueError(secret)):
        assert secret not in llm_service._gemini_error_class(exc)


def test_fallback_warning_logs_class_not_body(caplog):
    secret = "user context must not appear in logs"
    models = FakeModels(errors={"dead": ApiError(secret, 404, "NOT_FOUND")}, texts={"good": "fine"})
    service = _service(models, ["dead", "good"])
    with caplog.at_level(logging.WARNING, logger="test_llm_error_classification"):
        assert asyncio.run(service.generate("hello")) == "fine"
    warning_text = " ".join(r.getMessage() for r in caplog.records)
    assert "not_found" in warning_text
    assert secret not in warning_text


# --- not_found cooldown ---

def test_not_found_model_marked_dead_and_skipped_next_call():
    models = FakeModels(errors={"dead": ApiError("gone", 404, "NOT_FOUND")}, texts={"good": "ok"})
    service = _service(models, ["dead", "good"])
    assert asyncio.run(service.generate("hello")) == "ok"
    assert asyncio.run(service.generate("again")) == "ok"
    assert models.calls == ["dead", "good", "good"]


def test_not_found_cooldown_expires_after_six_hours(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(llm_service.time, "monotonic", lambda: now[0])
    models = FakeModels(errors={"dead": ApiError("gone", 404, "NOT_FOUND")}, texts={"good": "ok"})
    service = _service(models, ["dead", "good"])
    assert asyncio.run(service.generate("hello")) == "ok"
    assert models.calls == ["dead", "good"]
    now[0] = 1000.0 + 6 * 60 * 60 + 1
    assert asyncio.run(service.generate("later")) == "ok"
    assert models.calls == ["dead", "good", "dead", "good"]


# --- transient errors are not cached ---

def test_transient_error_does_not_skip_model():
    models = FakeModels(errors={"flaky": ApiError("backend", 503, "UNAVAILABLE")}, texts={"good": "ok"})
    service = _service(models, ["flaky", "good"])
    assert asyncio.run(service.generate("one")) == "ok"
    assert asyncio.run(service.generate("two")) == "ok"
    assert models.calls == ["flaky", "good", "flaky", "good"]


# --- quota behavior unchanged ---

def test_all_quota_still_raises_quota_exhausted():
    models = FakeModels(errors={
        "a": ApiError("quota", 429, "RESOURCE_EXHAUSTED"),
        "b": ApiError("quota", 429, "RESOURCE_EXHAUSTED"),
    })
    service = _service(models, ["a", "b"])
    with pytest.raises(QuotaExhausted):
        asyncio.run(service.generate("hello"))
    assert models.calls == ["a", "b"]


# --- outreach provider-side abort predicate ---

def test_provider_side_failure_predicate():
    assert _provider_side_failure(QuotaExhausted("quota"))
    assert _provider_side_failure(ApiError("gone", 404))
    assert _provider_side_failure(ApiError("limited", 429))
    assert not _provider_side_failure(ApiError("flaky", 503))
    assert not _provider_side_failure(ValueError("item-specific bug"))
    assert not _provider_side_failure(ApiError("no code"))
