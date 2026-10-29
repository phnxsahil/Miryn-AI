"""Regression tests for preset persistence and merge semantics.

Bug: _insert_identity_sql merged updates against a snapshot read before the
insert, then reused that stale merge on the IntegrityError retry. A slow
background update (e.g. the reflection worker) racing a Personalize save
silently reverted the user's preset. The fix re-merges against the latest
row inside the retry loop.
"""
import os
import sys
from contextlib import contextmanager

import pytest

sys.path.append(os.path.join(os.getcwd(), "miryn/backend"))

from app.services import identity_engine as ie  # noqa: E402


class _FakeMappings:
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return _FakeMappings(self._row)


class _FakeStore:
    def __init__(self):
        self.items = []

    def load(self, user_id, identity_id, sql_session=None):
        return list(self.items)

    def replace(self, user_id, identity_id, items, sql_session=None):
        self.items = list(items)


class _FakeInsertResult:
    def __init__(self, rowcount):
        self.rowcount = rowcount


from contextlib import contextmanager as _contextmanager


class _FakeSession:
    """Minimal session double: serves the latest identity row and applies the
    optimistic-concurrency guard on INSERT - zero rows when the payload's
    expected_version no longer matches the latest committed version."""

    def __init__(self, latest_row):
        self.latest_row = latest_row
        self.insert_attempts = 0
        self.insert_payloads = []

    @_contextmanager
    def begin_nested(self):
        yield self

    def execute(self, stmt, params=None):
        sql = str(stmt).lstrip()
        if sql.startswith("SELECT * FROM identities WHERE user_id"):
            return _FakeResult(self.latest_row)
        if sql.startswith("INSERT INTO identities"):
            self.insert_attempts += 1
            self.insert_payloads.append(dict(params))
            expected = params.get("expected_version")
            current_version = self.latest_row["version"] if self.latest_row else 0
            return _FakeInsertResult(1 if expected == current_version else 0)
        if sql.startswith("SELECT * FROM identities WHERE id"):
            return _FakeResult(self.latest_row)
        if sql.startswith("INSERT INTO identity_evolution_log"):
            return _FakeResult(None)
        raise AssertionError("unexpected SQL: %s" % sql[:80])


def _engine(monkeypatch, session):
    engine = ie.IdentityEngine.__new__(ie.IdentityEngine)
    engine.beliefs = _FakeStore()
    engine.open_loops = _FakeStore()
    engine.patterns = _FakeStore()
    engine.emotions = _FakeStore()
    engine.conflicts = _FakeStore()
    engine.supabase = None
    engine.reflection = None
    monkeypatch.setattr(ie, "has_sql", lambda: True)

    @contextmanager
    def fake_scope():
        yield session

    monkeypatch.setattr(ie, "get_sql_session", lambda: fake_scope())
    return engine


def _latest_row(preset):
    return {
        "id": "row-1",
        "user_id": "user-1",
        "version": 7,
        "state": "active",
        "traits": {},
        "values": {},
        "beliefs": "[]",
        "open_loops": "[]",
        "preset": preset,
        "memory_weights": "{}",
    }


def test_stale_worker_update_does_not_revert_preset_on_retry(monkeypatch):
    """A Personalize save landing between the worker's read and its insert
    must not be reverted: the version guard rejects the stale insert and the
    retry re-merges against the fresh row."""
    stale = _latest_row("companion")
    stale["version"] = 7
    fresh = dict(stale)
    fresh["id"] = "row-2"
    fresh["version"] = 8
    fresh["preset"] = "mirror"

    session = _FakeSession(stale)
    engine = _engine(monkeypatch, session)

    original_execute = session.execute
    selects = {"count": 0}

    def execute_with_concurrent_save(stmt, params=None):
        result = original_execute(stmt, params)
        if str(stmt).lstrip().startswith("SELECT * FROM identities WHERE user_id"):
            selects["count"] += 1
            # Simulate the user's preset save committing after the worker's
            # merge-read (get_identity's existence read is select #1, the
            # insert loop's read is select #2).
            if selects["count"] == 2:
                session.latest_row = fresh
        return result

    session.execute = execute_with_concurrent_save

    result = engine.update_identity("user-1", {"emotions": [{"primary_emotion": "calm"}]})

    assert session.insert_attempts == 2  # stale insert rejected, retry re-merged
    first_payload = session.insert_payloads[0]
    final_payload = session.insert_payloads[-1]
    assert first_payload["preset"] == "companion"  # merged from the stale read
    assert first_payload["expected_version"] == 7
    assert final_payload["preset"] == "mirror"  # re-merged from the fresh row
    assert final_payload["expected_version"] == 8
    assert result["preset"] == "mirror"


def test_merge_replace_drops_stale_preset_trait_keys():
    engine = ie.IdentityEngine.__new__(ie.IdentityEngine)
    current = {
        "state": "active",
        "traits": {"warmth": 0.95, "empathy": 0.9, "neutrality": 0.95},
        "values": {},
        "beliefs": [{"topic": "core_belief", "belief": "pace"}],
        "open_loops": [],
        "patterns": [],
        "emotions": [],
        "conflicts": [],
        "preset": "companion",
        "memory_weights": {"emotions": 0.5, "beliefs": 0.2},
    }
    updates = {
        "state": "active",
        "traits": {"neutrality": 0.95, "reflectiveness": 0.95},
        "memory_weights": {"beliefs": 0.4, "emotions": 0.3},
        "preset": "mirror",
        "_replace": ["traits", "values", "memory_weights"],
    }
    merged = engine._merge_identity(current, updates)
    assert merged["traits"] == {"neutrality": 0.95, "reflectiveness": 0.95}
    assert "warmth" not in merged["traits"]
    assert "empathy" not in merged["traits"]
    assert merged["memory_weights"] == {"beliefs": 0.4, "emotions": 0.3}
    assert merged["preset"] == "mirror"
    # beliefs not touched by the update -> preserved
    assert merged["beliefs"] == [{"topic": "core_belief", "belief": "pace"}]


def test_merge_without_replace_keeps_union_behaviour():
    engine = ie.IdentityEngine.__new__(ie.IdentityEngine)
    current = {"traits": {"warmth": 0.9}, "preset": "companion"}
    updates = {"traits": {"directness": 0.6}}
    merged = engine._merge_identity(current, updates)
    assert merged["traits"] == {"warmth": 0.9, "directness": 0.6}
    assert merged["preset"] == "companion"
