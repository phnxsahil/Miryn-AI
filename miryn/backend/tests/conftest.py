"""Test-wide safety defaults: never spend a real provider key accidentally."""

import os
from contextvars import ContextVar

import pytest


_DUMMY_KEY = "test-key-not-real"
_KEY_NAMES = (
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "VERTEX_PROJECT_ID",
)

for _name in _KEY_NAMES:
    os.environ[_name] = _DUMMY_KEY
os.environ["LLM_PROVIDER"] = "openai"
os.environ["OPENAI_BASE_URL"] = "http://127.0.0.1:9/v1"

if any(os.environ.get(_name) != _DUMMY_KEY for _name in _KEY_NAMES):
    pytest.exit("real LLM key present in test env", 2)


_current_item: ContextVar[pytest.Item | None] = ContextVar("current_test_item", default=None)


def pytest_runtest_setup(item: pytest.Item) -> None:
    _current_item.set(item)


def pytest_runtest_teardown(item: pytest.Item) -> None:
    _current_item.set(None)


@pytest.fixture(scope="session", autouse=True)
def block_real_llm():
    from app.services.llm_service import LLMService
    monkeypatch = pytest.MonkeyPatch()

    original_generate = LLMService.generate
    original_stream_chat = LLMService.stream_chat

    async def guarded_generate(self, *args, **kwargs):
        item = _current_item.get()
        if item is not None and item.get_closest_marker("live_llm") is not None:
            return await original_generate(self, *args, **kwargs)
        raise RuntimeError("Tests must not call a real LLM; mock LLMService in this test")

    async def guarded_stream_chat(self, *args, **kwargs):
        item = _current_item.get()
        if item is not None and item.get_closest_marker("live_llm") is not None:
            async for chunk in original_stream_chat(self, *args, **kwargs):
                yield chunk
            return
        raise RuntimeError("Tests must not call a real LLM; mock LLMService in this test")

    if LLMService.generate is original_generate:
        monkeypatch.setattr(LLMService, "generate", guarded_generate)
    if LLMService.stream_chat is original_stream_chat:
        monkeypatch.setattr(LLMService, "stream_chat", guarded_stream_chat)

    yield
    monkeypatch.undo()


@pytest.fixture(autouse=True)
def reset_llm_quota_state():
    from app.services import llm_service

    with llm_service._quota_lock:
        llm_service._quota_dead_until = 0.0
        llm_service._model_quota_dead_until.clear()
    yield
    with llm_service._quota_lock:
        llm_service._quota_dead_until = 0.0
        llm_service._model_quota_dead_until.clear()
