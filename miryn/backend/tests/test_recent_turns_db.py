"""DB-backed checks (real PostgreSQL via pgserver, real encryption) for recent-turn recall.

Fictional rows only. Verifies scoping, privacy, ordering, dedupe and prompt assembly.
They do NOT evaluate model behaviour.
"""
import uuid
from datetime import datetime, timedelta

import pytest

pgserver = pytest.importorskip("pgserver")
from cryptography.fernet import Fernet
from sqlalchemy import text

from app.config import settings
from app.core import database
from app.core.encryption import encrypt_text
from app.services.llm_service import LLMService
from app.services.memory_layer import MemoryLayer

U1, U2 = str(uuid.uuid4()), str(uuid.uuid4())
C1, C2 = str(uuid.uuid4()), str(uuid.uuid4())
BASE = datetime(2026, 11, 1, 10, 0, 0)

DDL = """CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), conversation_id UUID NOT NULL, user_id UUID NOT NULL,
  role VARCHAR(20) NOT NULL, content TEXT, memory_tier VARCHAR(20) NOT NULL DEFAULT 'episodic',
  delete_at TIMESTAMP, content_encrypted TEXT, created_at TIMESTAMP DEFAULT NOW())"""


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
        conn.execute(text(DDL))
    yield database._db.engine
    with database._db.engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS messages"))
    database._db.engine = None
    database._db.SessionLocal = None


def _add(engine, user, cid, role, content, minutes, encrypted=True, delete_at=None):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO messages (conversation_id, user_id, role, content, content_encrypted, created_at, delete_at)"
                 " VALUES (:c, :u, :r, :pt, :enc, :t, :d)"),
            {"c": cid, "u": user, "r": role, "pt": None if encrypted else content,
             "enc": encrypt_text(content) if encrypted else None, "t": BASE + timedelta(minutes=minutes), "d": delete_at},
        )


def _layer():
    return MemoryLayer.__new__(MemoryLayer)


def test_returns_latest_turns_oldest_first_decrypted(engine):
    for i in range(6):
        _add(engine, U1, C1, "user" if i % 2 == 0 else "assistant", f"turn {i}", i, encrypted=(i % 2 == 0))
    turns = _layer().recent_turns(U1, C1, 4)
    assert [t["content"] for t in turns] == ["turn 2", "turn 3", "turn 4", "turn 5"]
    assert [t["role"] for t in turns] == ["user", "assistant", "user", "assistant"]


def test_never_returns_another_users_or_conversation_rows(engine):
    _add(engine, U1, C1, "user", "mine", 0)
    _add(engine, U2, C1, "user", "someone elses same conversation id", 1)
    _add(engine, U1, C2, "user", "my other conversation", 2)
    assert [t["content"] for t in _layer().recent_turns(U1, C1, 8)] == ["mine"]


def test_skips_expired_and_drops_the_message_being_answered(engine):
    _add(engine, U1, C1, "user", "expired", 0, delete_at=datetime(2000, 1, 1))
    _add(engine, U1, C1, "assistant", "earlier reply", 1)
    _add(engine, U1, C1, "user", "what I am asking now", 2)
    turns = _layer().recent_turns(U1, C1, 8, exclude_text="what I am asking now")
    assert [t["content"] for t in turns] == ["earlier reply"]


def test_off_by_default_and_safe_without_conversation(engine):
    assert settings.RECENT_TURNS_LIMIT == 0
    assert _layer().recent_turns(U1, None, 8) == []
    assert _layer().recent_turns(U1, C1, 0) == []


def test_prompt_block_uses_real_rows_and_removes_duplicate_memories(engine):
    _add(engine, U1, C1, "user", "my sister Anaya starts chemo tomorrow", 0)
    _add(engine, U1, C1, "assistant", "that is a lot to carry tonight", 1)
    turns = _layer().recent_turns(U1, C1, 8)
    memories = [{"id": turns[0]["id"], "role": "user", "content": turns[0]["content"], "created_at": "t"},
                {"id": "other", "role": "user", "content": "an older unrelated memory", "created_at": "t0"}]
    out = LLMService()._format_context({"known_facts": [], "memories": memories, "recent_turns": turns})
    assert "User: my sister Anaya starts chemo tomorrow" in out
    assert "Miryn: that is a lot to carry tonight" in out
    assert out.count("my sister Anaya") == 1
    assert "an older unrelated memory" in out
    assert out.index("Recent turns") < out.index("Relevant past conversations")
