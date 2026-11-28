"""Messages the user deleted must not re-enter the reply prompt.

User-facing deletion paths (memory delete, episodic purge, retention expiry)
set delete_at and the nightly worker hard-deletes later. fetch_recent_turns
must honor delete_at now, or deleted content would keep surfacing in the
"Conversation so far" section until the worker runs.
"""
import asyncio

from sqlalchemy import create_engine, text

from app.services.recent_turns import fetch_recent_turns


def _engine_with_rows():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE messages (id TEXT PRIMARY KEY, conversation_id TEXT, role TEXT, content TEXT, content_encrypted TEXT, created_at TEXT, delete_at TEXT)"
        ))
        rows = [
            ("m1", "kept null", None),
            ("m2", "deleted past", "2020-01-01T00:00:00+00:00"),
            ("m3", "kept future", "2999-01-01T00:00:00+00:00"),
        ]
        connection.execute(
            text("INSERT INTO messages (id, conversation_id, role, content, created_at, delete_at) VALUES (:id, 'c1', 'user', :content, :created_at, :delete_at)"),
            [{"id": i, "content": c, "created_at": "2026-01-01T00:00:0" + i[-1], "delete_at": d} for i, c, d in rows],
        )
    return engine


def test_deleted_messages_are_excluded_from_recent_turns(monkeypatch):
    monkeypatch.setattr("app.services.recent_turns.has_sql", lambda: True)
    engine = _engine_with_rows()
    with engine.connect() as connection:
        turns = asyncio.run(fetch_recent_turns("c1", sql_session=connection))
    contents = [t["content"] for t in turns]
    assert "kept null" in contents
    assert "kept future" in contents
    assert "deleted past" not in contents
