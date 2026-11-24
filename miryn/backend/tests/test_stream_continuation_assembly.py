"""Reply assembly in /chat/stream: complete Unicode endings must not trigger a continuation call."""
import asyncio
import json

import pytest

import app.api.chat as chat


class FakeLLM:
    def __init__(self, chunks, completion=""):
        self.chunks, self.completion, self.calls = chunks, completion, 0

    async def stream_chat(self, **kw):
        for c in self.chunks:
            yield c

    async def complete_sentence(self, text, identity):
        self.calls += 1
        return self.completion


def _run(monkeypatch, chunks, completion=""):
    llm = FakeLLM(chunks, completion)
    monkeypatch.setattr(chat, "has_sql", lambda: False)
    monkeypatch.setattr(chat, "_create_conversation_with_fallback", lambda *a, **k: "conv-1")
    monkeypatch.setattr(chat, "_touch_conversation_updated_at", lambda *a, **k: None)

    async def prep(*a, **k):
        return {}, []

    async def noop(*a, **k):
        return None

    monkeypatch.setattr(chat, "_prepare_stream_context", prep)
    monkeypatch.setattr(chat, "_enforce_message_rate_limit", noop)
    monkeypatch.setattr(chat, "_fire_and_forget", lambda coro, *a, **k: coro.close())
    monkeypatch.setattr(chat, "score_message_heuristic", lambda m: [])
    monkeypatch.setattr(chat.orchestrator, "llm", llm, raising=False)

    class FS:
        def list_top(self, *a, **k):
            return []

    monkeypatch.setattr(chat, "FactStore", FS)

    async def go():
        resp = await chat.stream_message(chat.ChatRequest(message="hi"), user_id="u1")
        out = []
        async for part in resp.body_iterator:
            out.append(part)
        return out

    events = asyncio.run(go())
    texts = [json.loads(e[6:]).get("chunk") for e in events if e.startswith("data: ")]
    return llm, "".join(t for t in texts if t)


@pytest.mark.parametrize("reply", [
    "That sounds heavy\u2026",
    "She said \u201cit is over.\u201d",
    "Main yahin hoon\u0964",
    "I am here.",
])
def test_complete_endings_make_no_continuation_call(monkeypatch, reply):
    llm, text = _run(monkeypatch, [reply])
    assert llm.calls == 0
    assert text == reply


def test_incomplete_reply_still_uses_continuation(monkeypatch):
    llm, text = _run(monkeypatch, ["That sounds like a lot and"], completion="you carried it alone.")
    assert llm.calls == 1
    assert text.endswith("you carried it alone.")


def test_incomplete_reply_with_empty_completion_gets_period(monkeypatch):
    llm, text = _run(monkeypatch, ["That sounds like a lot and"], completion="")
    assert llm.calls == 1
    assert text.endswith(".")
