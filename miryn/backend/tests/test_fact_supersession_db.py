"""DB-backed tests for explicit-correction linking.

Runs link_explicit_corrections against a real PostgreSQL database (via the
pgserver test fixture) with real Fernet encryption and the real migration
files (011 + 013), covering the transaction, audit row, rollback, and the
partial-unique-index behavior that pure resolver unit tests cannot prove.
"""

import json
import uuid
from datetime import datetime, timedelta

import pgserver
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import text

from app.config import settings
from app.core import database
from app.core.encryption import decrypt_text, encrypt_text
from app.services.fact_store import FactStore
from app.services.importance import ScoredFact, fact_key

OLD_TEXT = "Training for a triathlon in Goa on December 14"
NEW_TEXT = "Training for a triathlon in Goa on January 11"
CORRECTS = {
    "entity": "Goa triathlon",
    "attribute": "date",
    "old_value": "December 14",
    "new_value": "January 11",
    "polarity_old": "neutral",
    "polarity_new": "neutral",
}
USER = str(uuid.uuid4())
MSG1 = str(uuid.uuid4())
MSG2 = str(uuid.uuid4())

USERS_STUB = "CREATE TABLE IF NOT EXISTS users (id UUID PRIMARY KEY DEFAULT gen_random_uuid());"
MIGRATIONS = ["migrations/011_memory_facts.sql", "migrations/013_fact_supersession.sql"]


@pytest.fixture(scope="module")
def pg(tmp_path_factory):
    server = pgserver.get_server(tmp_path_factory.mktemp("pg"))
    yield server
    server.cleanup()


@pytest.fixture()
def db(pg, monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", pg.get_uri())
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setattr(settings, "MEMORY_SUPERSESSION_ENABLED", True)
    database._db = database.Database()
    with database._db.engine.begin() as conn:
        conn.execute(text(USERS_STUB))
        conn.execute(text("INSERT INTO users (id) VALUES (:id)"), {"id": USER})
        for migration in MIGRATIONS:
            for statement in open(migration).read().split(";"):
                if statement.strip():
                    conn.execute(text(statement))
    yield database._db.engine
    with database._db.engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS memory_fact_supersessions, memory_facts, users CASCADE"))
    database._db.engine = None
    database._db.SessionLocal = None


def _seed_fact(engine, text_value, *, extractor="llm", category="goal", age_hours=2):
    fact_id = str(uuid.uuid4())
    created = datetime(2026, 10, 31, 6, 0, 0) - timedelta(hours=age_hours)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO memory_facts (id, user_id, fact, fact_key, category, importance,
                                          extractor, created_at)
                VALUES (:id, :user_id, :fact, :fact_key, :category, 0.9, :extractor, :created_at)
                """
            ),
            {
                "id": fact_id,
                "user_id": USER,
                "fact": encrypt_text(text_value),
                "fact_key": fact_key(text_value),
                "category": category,
                "extractor": extractor,
                "created_at": created,
            },
        )
    return fact_id


def _rows(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).mappings().all()


def _new_scored_fact():
    return ScoredFact(NEW_TEXT, "goal", 0.9, 0.0, "llm", dict(CORRECTS))


def test_link_supersedes_unique_candidate_with_audit_row(db):
    old_id = _seed_fact(db, OLD_TEXT)
    store = FactStore()
    new_fact = _new_scored_fact()
    store.upsert_facts(USER, [new_fact], MSG1)

    links = store.link_explicit_corrections(USER, [new_fact], MSG1)

    assert len(links) == 1 and links[0]["old_fact_id"] == old_id
    old = _rows(db, "SELECT status, superseded_by FROM memory_facts WHERE id = :id", id=old_id)[0]
    assert old["status"] == "superseded"
    assert str(old["superseded_by"]) == links[0]["new_fact_id"]
    audits = _rows(db, "SELECT * FROM memory_fact_supersessions WHERE user_id = :u", u=USER)
    assert len(audits) == 1
    assert str(audits[0]["old_fact_id"]) == old_id
    assert str(audits[0]["new_fact_id"]) == links[0]["new_fact_id"]
    # Encryption parity: the audit payload is Fernet-encrypted at rest, so
    # the raw column must not leak the user's values as plaintext JSONB.
    raw_corrects = audits[0]["corrects"]
    assert isinstance(raw_corrects, str)
    assert "January 11" not in raw_corrects
    assert "December 14" not in raw_corrects
    payload = json.loads(decrypt_text(raw_corrects))
    assert payload["new_value"] == "January 11"
    assert payload["old_value"] == "December 14"
    # Readers only see active rows: the stale date is hidden, the new one shows.
    visible = [row["content"] for row in store.list_top(USER, 10)]
    assert visible == [NEW_TEXT]


def test_ambiguity_leaves_everything_active(db):
    _seed_fact(db, OLD_TEXT)
    _seed_fact(db, "The Goa triathlon happens December 14", age_hours=5)
    store = FactStore()
    new_fact = _new_scored_fact()
    store.upsert_facts(USER, [new_fact], MSG1)

    assert store.link_explicit_corrections(USER, [new_fact], MSG1) == []
    active = _rows(db, "SELECT id FROM memory_facts WHERE user_id = :u AND status = 'active'", u=USER)
    assert len(active) == 3
    assert not _rows(db, "SELECT id FROM memory_fact_supersessions WHERE user_id = :u", u=USER)


def test_manual_memory_is_never_superseded(db):
    _seed_fact(db, OLD_TEXT, extractor="manual")
    store = FactStore()
    new_fact = _new_scored_fact()
    store.upsert_facts(USER, [new_fact], MSG1)

    assert store.link_explicit_corrections(USER, [new_fact], MSG1) == []
    active = _rows(db, "SELECT id FROM memory_facts WHERE user_id = :u AND status = 'active'", u=USER)
    assert len(active) == 2


def test_failed_audit_insert_rolls_back_status_flip(db):
    _seed_fact(db, OLD_TEXT)
    store = FactStore()
    new_fact = _new_scored_fact()
    store.upsert_facts(USER, [new_fact], MSG1)
    with db.begin() as conn:
        conn.execute(text("ALTER TABLE memory_fact_supersessions ADD COLUMN broken TEXT NOT NULL"))

    with pytest.raises(Exception):
        store.link_explicit_corrections(USER, [new_fact], MSG1)

    active = _rows(db, "SELECT id FROM memory_facts WHERE user_id = :u AND status = 'active'", u=USER)
    assert len(active) == 2, "status flip must roll back when the audit insert fails"


def test_supersede_frees_unique_slot_for_restated_old_text(db):
    _seed_fact(db, OLD_TEXT)
    store = FactStore()
    new_fact = _new_scored_fact()
    store.upsert_facts(USER, [new_fact], MSG1)
    store.link_explicit_corrections(USER, [new_fact], MSG1)

    # Re-stating the old text must insert cleanly: the partial unique index
    # only covers status = 'active' rows.
    store.upsert_facts(USER, [ScoredFact(OLD_TEXT, "goal", 0.9, 0.0, "llm")], MSG2)

    rows = _rows(
        db,
        "SELECT status FROM memory_facts WHERE user_id = :u AND fact_key = :k ORDER BY status",
        u=USER,
        k=fact_key(OLD_TEXT),
    )
    assert [row["status"] for row in rows] == ["active", "superseded"]


def test_repeated_correction_does_not_double_link(db):
    """Idempotency: linking the same message twice must not error or double-record."""
    old_id = _seed_fact(db, OLD_TEXT)
    store = FactStore()
    new_fact = _new_scored_fact()
    store.upsert_facts(USER, [new_fact], MSG1)

    first = store.link_explicit_corrections(USER, [new_fact], MSG1)
    second = store.link_explicit_corrections(USER, [new_fact], MSG1)

    assert len(first) == 1
    assert second == [], "old fact is already superseded, so no eligible candidate remains"
    assert str(_rows(db, "SELECT status FROM memory_facts WHERE id = :id", id=old_id)[0]["status"]) == "superseded"
    assert len(_rows(db, "SELECT id FROM memory_fact_supersessions WHERE user_id = :u", u=USER)) == 1


def test_linking_disabled_by_flag_leaves_everything_active(db, monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_SUPERSESSION_ENABLED", False)
    _seed_fact(db, OLD_TEXT)
    store = FactStore()
    new_fact = _new_scored_fact()
    store.upsert_facts(USER, [new_fact], MSG1)

    assert store.link_explicit_corrections(USER, [new_fact], MSG1) == []
    active = _rows(db, "SELECT id FROM memory_facts WHERE user_id = :u AND status = 'active'", u=USER)
    assert len(active) == 2
    assert not _rows(db, "SELECT id FROM memory_fact_supersessions WHERE user_id = :u", u=USER)


def _link_one(db):
    old_id = _seed_fact(db, OLD_TEXT)
    store = FactStore()
    new_fact = _new_scored_fact()
    store.upsert_facts(USER, [new_fact], MSG1)
    links = store.link_explicit_corrections(USER, [new_fact], MSG1)
    assert len(links) == 1
    return store, old_id, links[0]["new_fact_id"]


def test_restore_superseded_reactivates_and_marks_audit(db):
    store, old_id, _ = _link_one(db)

    assert store.restore_superseded(USER, old_id) == "restored"

    row = _rows(db, "SELECT status, superseded_by FROM memory_facts WHERE id = :id", id=old_id)[0]
    assert row["status"] == "active" and row["superseded_by"] is None
    audit = _rows(db, "SELECT restored_at FROM memory_fact_supersessions WHERE old_fact_id = :id", id=old_id)[0]
    assert audit["restored_at"] is not None
    visible = sorted(row["content"] for row in store.list_top(USER, 10))
    assert visible == sorted([OLD_TEXT, NEW_TEXT])


def test_restore_after_old_text_restated_is_a_safe_conflict(db):
    store, old_id, _ = _link_one(db)
    # User re-states the old text: the partial unique index frees the slot,
    # and a new active row with the same fact_key now exists.
    store.upsert_facts(USER, [ScoredFact(OLD_TEXT, "goal", 0.9, 0.0, "llm")], MSG2)

    assert store.restore_superseded(USER, old_id) == "conflict"

    row = _rows(db, "SELECT status FROM memory_facts WHERE id = :id", id=old_id)[0]
    assert row["status"] == "superseded", "conflicting restore must be a no-op"


def test_restore_unknown_fact_is_not_found(db):
    assert FactStore().restore_superseded(USER, str(uuid.uuid4())) == "not_found"


def test_list_supersessions_returns_decrypted_history(db):
    store, old_id, new_id = _link_one(db)

    history = store.list_supersessions(USER, 10)

    assert len(history) == 1
    entry = history[0]
    assert entry["old_fact_id"] == old_id
    assert entry["new_fact_id"] == new_id
    assert entry["corrects"]["new_value"] == "January 11"
    assert entry["restored_at"] is None


def test_soft_delete_removes_referencing_audit_rows(db):
    store, old_id, new_id = _link_one(db)

    assert store.soft_delete(USER, new_id) is True

    assert not _rows(db, "SELECT id FROM memory_fact_supersessions WHERE user_id = :u", u=USER)
