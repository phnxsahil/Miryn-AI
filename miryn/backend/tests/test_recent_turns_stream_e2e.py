"""Stream endpoint end to end against real PostgreSQL (pgserver) and real encryption.

Real: owner validation SQL, recent_turns query, decryption, request flag, timeout, fail-open.
Stubbed: the model call (captures the context it would get), fact store, background jobs.
Fictional rows only. These do NOT evaluate model behaviour.
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

pgserver = pytest.importorskip("pgserver")
from cryptography.fernet import Fernet
from sqlalchemy import text

from app.api import chat
from app.api.chat import ChatRequest
from app.config import settings
from app.core import database
from app.core.encryption import encrypt_text

U1, U2 = str(uuid.uuid4()), str(uuid.uuid4())
C1, C2 = str(uuid.uuid4()), str(uuid.uuid4())
BASE = datetime(2026, 11, 1, 10, 0, 0)


@pytest.fixture(scope="module")
def pg(tmp_path_factory):
    server = pgserver.get_server(tmp_path_factory.mktemp("pg"))
    yield server
    server.cleanup()


@pytest.fixture()
def engine(pg, monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", pg.get_uri())
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", Fernet.generate_key().decode())
    database._db = database.Database()
    with database._db.engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS messages"))
        conn.execute(text("DROP TABLE IF EXISTS conversations"))
        conn.execute(text("CREATE TABLE conversations (id UUID PRIMARY KEY, user_id UUID NOT NULL)"))
        conn.execute(text(
            "CREATE TABLE messages (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), conversation_id UUID NOT NULL,"
            " user_id UUID NOT NULL, role VARCHAR(20) NOT NULL, content TEXT, memory_tier VARCHAR(20) NOT NULL DEFAULT 'episodic',"
            " delete_at TIMESTAMP, content_encrypted TEXT, created_at TIMESTAMP DEFAULT NOW())"))
        conn.execute(text("INSERT INTO conversations VALUES (:c, :u)"), [{"c": C1, "u": U1}, {"c": C2, "u": U2}])
    yield database._db.engine
    with database._db.engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS messages"))
        conn.execute(text("DROP TABLE IF EXISTS conversations"))
    database._db.engine = None
    database._db.SessionLocal = None


def _add(engine, user, cid, role, content, minutes, delete_at=None):
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO messages (conversation_id, user_id, role, content_encrypted, created_at, delete_at)"
            " VALUES (:c, :u, :r, :e, :t, :d)"),
            {"c": cid, "u": user, "r": role, "e": encrypt_text(content), "t": BASE + timedelta(minutes=minutes), "d": delete_at})


def _stream(user, cid, message, recent_override=None):
    captured = {}

    async def fake_stream_chat(*args, **kwargs):
        captured.update(kwargs)
        yield "ok."

    async def exercise():
        response = await chat.stream_message(ChatRequest(message=message, conversation_id=cid), user)
        return [e async for e in response.body_iterator]

    with patch("app.api.chat._enforce_message_rate_limit", new=AsyncMock()), \
         patch("app.api.chat._prepare_stream_context", new=AsyncMock(return_value=({}, []))), \
         patch("app.api.chat._touch_conversation_updated_at"), \
         patch("app.api.chat.score_message_heuristic", return_value=[]), \
         patch("app.api.chat.FactStore") as fs, \
         patch("app.api.chat._store_stream_facts", new=AsyncMock()), \
         patch("app.api.chat.orchestrator.llm.stream_chat", fake_stream_chat), \
         patch("app.api.chat._fire_and_forget", side_effect=lambda coro, label, uid: coro.close()), \
         patch("app.api.chat._background_stream_postprocess", new=AsyncMock()):
        fs.return_value.list_top.return_value = []
        if recent_override is not None:
            with patch("app.api.chat.orchestrator.memory.recent_turns", recent_override):
                asyncio.run(exercise())
        else:
            asyncio.run(exercise())
    return captured.get("context")


def test_enabled_returns_decrypted_turns_of_this_conversation_only(engine, monkeypatch):
    monkeypatch.setattr(settings, "RECENT_TURNS_LIMIT", 8)
    _add(engine, U1, C1, "user", "my sister Anaya starts chemo tomorrow", 0)
    _add(engine, U1, C1, "assistant", "that is a lot to carry tonight", 1)
    _add(engine, U2, C2, "user", "other user's private line", 2)
    _add(engine, U1, C1, "user", "can you remind me why tomorrow matters", 3)  # the current message, already stored
    ctx = _stream(U1, C1, "can you remind me why tomorrow matters")
    assert [t["content"] for t in ctx["recent_turns"]] == ["my sister Anaya starts chemo tomorrow", "that is a lot to carry tonight"]
    assert "private line" not in str(ctx)


def test_default_off_sends_no_recent_turns(engine, monkeypatch):
    monkeypatch.setattr(settings, "RECENT_TURNS_LIMIT", 0)
    _add(engine, U1, C1, "user", "my sister Anaya starts chemo tomorrow", 0)
    ctx = _stream(U1, C1, "hello")
    assert ctx["recent_turns"] == []


def test_guessing_another_users_conversation_id_is_refused_and_leaks_nothing(engine, monkeypatch):
    monkeypatch.setattr(settings, "RECENT_TURNS_LIMIT", 8)
    _add(engine, U2, C2, "user", "other user's private line", 0)
    with pytest.raises(HTTPException) as err:
        _stream(U1, C2, "hello")
    assert err.value.status_code == 403


def test_expired_rows_are_skipped(engine, monkeypatch):
    monkeypatch.setattr(settings, "RECENT_TURNS_LIMIT", 8)
    _add(engine, U1, C1, "user", "expired line", 0, delete_at=datetime(2020, 1, 1))
    _add(engine, U1, C1, "user", "kept line", 1)
    ctx = _stream(U1, C1, "hello")
    assert [t["content"] for t in ctx["recent_turns"]] == ["kept line"]


def test_undecryptable_row_does_not_break_the_reply(engine, monkeypatch):
    monkeypatch.setattr(settings, "RECENT_TURNS_LIMIT", 8)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO messages (conversation_id, user_id, role, content_encrypted, created_at)"
                          " VALUES (:c, :u, 'user', 'not-valid-ciphertext', :t)"), {"c": C1, "u": U1, "t": BASE})
    _add(engine, U1, C1, "user", "readable line", 1)
    ctx = _stream(U1, C1, "hello")
    contents = [t["content"] for t in ctx["recent_turns"]]
    assert "readable line" in contents and "not-valid-ciphertext" not in contents


def test_retrieval_error_fails_open_with_empty_turns(engine, monkeypatch):
    monkeypatch.setattr(settings, "RECENT_TURNS_LIMIT", 8)
    def boom(*a, **k):
        raise RuntimeError("db down")
    ctx = _stream(U1, C1, "hello", recent_override=boom)
    assert ctx["recent_turns"] == []


def test_slow_retrieval_times_out_and_reply_continues(engine, monkeypatch):
    import time
    monkeypatch.setattr(settings, "RECENT_TURNS_LIMIT", 8)
    monkeypatch.setattr(settings, "RECENT_TURNS_TIMEOUT_SECONDS", 0.05)
    def slow(*a, **k):
        time.sleep(0.3)
        return [{"role": "user", "content": "late"}]
    started = time.perf_counter()
    ctx = _stream(U1, C1, "hello", recent_override=slow)
    assert ctx["recent_turns"] == []
    assert time.perf_counter() - started < 1.5
