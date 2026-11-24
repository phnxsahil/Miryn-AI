"""Wiring checks: recent turns reach the model call on the stream and non-stream paths.

Mocked storage and model, fictional turns. They do NOT evaluate model behaviour.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api import chat
from app.api.chat import ChatRequest
from app.config import settings
from app.services.orchestrator import ConversationOrchestrator

TURNS = [
    {"id": "t1", "role": "user", "content": "my sister Anaya starts chemo tomorrow"},
    {"id": "t2", "role": "assistant", "content": "that is a lot to carry tonight"},
]


def _run_stream(recent_turns_mock):
    captured = {}

    async def fake_stream_chat(*args, **kwargs):
        captured.update(kwargs)
        yield "ok."

    scheduled = []

    async def exercise():
        response = await chat.stream_message(ChatRequest(message="can you remind me why tomorrow matters"), "u1")
        return [e async for e in response.body_iterator]

    with patch("app.api.chat._enforce_message_rate_limit", new=AsyncMock()), \
         patch("app.api.chat.has_sql", return_value=False), \
         patch("app.api.chat._create_conversation_with_fallback", return_value="conv-1"), \
         patch("app.api.chat._touch_conversation_updated_at"), \
         patch("app.api.chat._prepare_stream_context", new=AsyncMock(return_value=({}, []))), \
         patch("app.api.chat.score_message_heuristic", return_value=[]), \
         patch("app.api.chat.FactStore") as fact_store, \
         patch("app.api.chat._store_stream_facts", new=AsyncMock()), \
         patch("app.api.chat.orchestrator.memory.recent_turns", recent_turns_mock), \
         patch("app.api.chat.orchestrator.llm.stream_chat", fake_stream_chat), \
         patch("app.api.chat.analyze_reflection.delay", return_value=None), \
         patch("app.api.chat._fire_and_forget", side_effect=lambda coro, label, uid: (scheduled.append(coro), coro.close())), \
         patch("app.api.chat._background_stream_postprocess", new=AsyncMock()):
        fact_store.return_value.list_top.return_value = []
        asyncio.run(exercise())
    return captured["context"]


def test_stream_passes_recent_turns_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "RECENT_TURNS_LIMIT", 8)
    mock = MagicMock(return_value=TURNS)
    ctx = _run_stream(mock)
    assert ctx["recent_turns"] == TURNS
    args = mock.call_args.args
    assert args[0] == "u1" and args[1] == "conv-1" and args[2] == 8
    assert args[4] == "can you remind me why tomorrow matters"


def test_stream_off_by_default_does_not_read_turns(monkeypatch):
    monkeypatch.setattr(settings, "RECENT_TURNS_LIMIT", 0)
    mock = MagicMock(return_value=TURNS)
    ctx = _run_stream(mock)
    assert ctx["recent_turns"] == [] and not mock.called


def test_stream_still_answers_when_turn_read_fails(monkeypatch):
    monkeypatch.setattr(settings, "RECENT_TURNS_LIMIT", 8)
    ctx = _run_stream(MagicMock(side_effect=RuntimeError("db down")))
    assert ctx["recent_turns"] == []


def test_stream_still_answers_when_turn_read_times_out(monkeypatch):
    import time
    monkeypatch.setattr(settings, "RECENT_TURNS_LIMIT", 8)
    monkeypatch.setattr(settings, "RECENT_TURNS_TIMEOUT_SECONDS", 0.05)
    ctx = _run_stream(MagicMock(side_effect=lambda *a: time.sleep(0.3) or TURNS))
    assert ctx["recent_turns"] == []


def _run_handle(monkeypatch, limit):
    monkeypatch.setattr(settings, "RECENT_TURNS_LIMIT", limit)
    orch = ConversationOrchestrator.__new__(ConversationOrchestrator)
    import logging
    orch.logger = logging.getLogger("t")
    orch.identity = MagicMock()
    orch.identity.get_identity.return_value = {}
    orch.identity.detect_conflicts = AsyncMock(return_value=[])
    orch.memory = MagicMock()
    orch.memory.retrieve_context = AsyncMock(return_value=[])
    orch.memory.store_conversation = AsyncMock(return_value=None)
    orch.memory.recent_turns = MagicMock(return_value=TURNS)
    captured = {}

    async def fake_chat(context, user_message, identity):
        captured["context"] = context
        raise RuntimeError("stop here")

    orch.llm = MagicMock()
    orch.llm.chat = fake_chat
    orch._get_cached_result = lambda *a, **k: None
    orch._cache_result = lambda *a, **k: None
    orch._assistant_idempotency_key = lambda k: k

    async def go():
        result = await orch.handle_message("u1", "can you remind me why tomorrow matters", "conv-1")
        await asyncio.sleep(0)
        return result

    with patch("app.services.orchestrator.FactStore") as fs, \
         patch("app.services.orchestrator.score_message_heuristic", return_value=[]):
        fs.return_value.list_top.return_value = []
        asyncio.run(go())
    return captured["context"], orch.memory.recent_turns


def test_non_stream_passes_recent_turns_when_enabled(monkeypatch):
    ctx, mock = _run_handle(monkeypatch, 8)
    assert ctx["recent_turns"] == TURNS
    assert mock.call_args.args[1] == "conv-1"


def test_non_stream_off_by_default(monkeypatch):
    ctx, mock = _run_handle(monkeypatch, 0)
    assert ctx["recent_turns"] == [] and not mock.called
