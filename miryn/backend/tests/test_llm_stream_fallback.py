import asyncio
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.llm_service import LLMService


pytestmark = pytest.mark.live_llm


class ApiError(Exception):
    def __init__(self, message: str, code: int, status: str):
        super().__init__(message)
        self.code = code
        self.status = status


def _chunk(text: str, finish_reason=None):
    candidates = [] if finish_reason is None else [SimpleNamespace(finish_reason=finish_reason)]
    return SimpleNamespace(text=text, candidates=candidates)


class FakeModels:
    def __init__(self, streams=None, errors=None):
        self.streams = streams or {}
        self.errors = errors or {}
        self.calls = []

    async def generate_content_stream(self, *, model, contents, config):
        self.calls.append(model)
        if model in self.errors:
            raise self.errors[model]
        result = self.streams.get(model, [])

        async def iterator():
            for item in result:
                if isinstance(item, Exception):
                    raise item
                yield item

        return iterator()


def _service(models, chain):
    service = LLMService.__new__(LLMService)
    service.provider = "gemini"
    service.logger = logging.getLogger("test_llm_stream_fallback")
    service.model = chain[0]
    service.gemini_fallback_models = chain
    service.client = SimpleNamespace(aio=SimpleNamespace(models=models))
    service._build_system_prompt = lambda identity: "system"
    service._format_context = lambda context: "context"
    service._build_user_prompt = lambda context, message: message
    return service


async def _collect(service):
    return [part async for part in service.stream_chat({}, "hello", {})]


def test_invalid_argument_is_not_classified_as_quota():
    models = FakeModels(errors={"primary": ApiError("INVALID_ARGUMENT in generateContent", 400, "INVALID_ARGUMENT")})
    service = _service(models, ["primary", "secondary"])

    with pytest.raises(ApiError):
        asyncio.run(_collect(service))

    assert models.calls == ["primary"]


def test_retryable_error_uses_next_streaming_model():
    models = FakeModels(
        errors={"primary": ApiError("quota", 429, "RESOURCE_EXHAUSTED")},
        streams={"secondary": [_chunk("Hello "), _chunk("there")]},
    )
    service = _service(models, ["primary", "secondary"])

    assert asyncio.run(_collect(service)) == ["Hello ", "there"]
    assert models.calls == ["primary", "secondary"]


def test_empty_stream_uses_next_model():
    models = FakeModels(
        streams={
            "primary": [_chunk("", finish_reason="STOP")],
            "secondary": [_chunk("Remembered "), _chunk("context")],
        }
    )
    service = _service(models, ["primary", "secondary"])

    assert asyncio.run(_collect(service)) == ["Remembered ", "context"]
    assert models.calls == ["primary", "secondary"]


def test_all_empty_streams_fall_back_to_progressive_generate():
    models = FakeModels(streams={"primary": [], "secondary": []})
    service = _service(models, ["primary", "secondary"])
    sentence = "A short sentence that is long enough to require multiple progressive chunks. " * 2
    service.generate = AsyncMock(return_value=sentence)

    parts = asyncio.run(_collect(service))

    assert len(parts) > 1
    assert "".join(parts) == sentence
    service.generate.assert_awaited_once()


def test_mid_stream_failure_does_not_switch_models():
    models = FakeModels(
        streams={
            "primary": [_chunk("first "), RuntimeError("connection closed")],
            "secondary": [_chunk("second")],
        }
    )
    service = _service(models, ["primary", "secondary"])

    assert asyncio.run(_collect(service)) == ["first "]
    assert models.calls == ["primary"]
