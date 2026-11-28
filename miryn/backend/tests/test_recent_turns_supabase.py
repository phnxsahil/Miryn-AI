"""Supabase REST path: encrypted-only rows are decrypted like the SQL path.

Production stores message content encrypted; rows can carry only
content_encrypted. The Supabase fallback path must select and decrypt that
column the same way the SQL path does, or recent turns silently vanish in
Supabase mode. A decrypt failure drops the turn; it never fails a reply.
"""
import asyncio

from app.services.recent_turns import fetch_recent_turns


class _FakeResponse:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, data):
        self._data = data
        self.selected = None

    def select(self, cols):
        self.selected = cols
        return self

    def eq(self, *args):
        return self

    def or_(self, *args):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args):
        return self

    def execute(self):
        return _FakeResponse(self._data)


class _FakeDB:
    def __init__(self, data):
        self.query = _FakeQuery(data)

    def table(self, name):
        return self.query


def _patch_supabase(monkeypatch, rows, decrypt):
    monkeypatch.setattr("app.services.recent_turns.has_sql", lambda: False)
    db = _FakeDB(rows)
    monkeypatch.setattr("app.services.recent_turns.get_db", lambda: db)
    monkeypatch.setattr("app.services.recent_turns.decrypt_text", decrypt)
    return db


def test_supabase_path_decrypts_encrypted_only_turns(monkeypatch):
    db = _patch_supabase(
        monkeypatch,
        [{"role": "user", "content": None, "content_encrypted": "enc1"}],
        lambda s: "decrypted-" + s,
    )
    turns = asyncio.run(fetch_recent_turns("c1"))
    assert [t["content"] for t in turns] == ["decrypted-enc1"]
    assert db.query.selected == "role, content, content_encrypted"


def test_supabase_path_decrypt_failure_drops_turn(monkeypatch):
    def _boom(_value):
        raise ValueError("bad ciphertext")

    _patch_supabase(
        monkeypatch,
        [{"role": "user", "content": None, "content_encrypted": "enc1"}],
        _boom,
    )
    assert asyncio.run(fetch_recent_turns("c1")) == []


def test_supabase_path_prefers_plaintext_when_present(monkeypatch):
    _patch_supabase(
        monkeypatch,
        [{"role": "user", "content": "plain", "content_encrypted": "enc1"}],
        lambda s: "decrypted-" + s,
    )
    turns = asyncio.run(fetch_recent_turns("c1"))
    assert [t["content"] for t in turns] == ["plain"]
