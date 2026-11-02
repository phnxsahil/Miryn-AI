"""DB-backed tests for read-path correction ordering.

Mirrors the live probe trace: a stale fact outranked its explicit correction
because the correction was stored with lower importance and the supersession
gate is OFF, so retrieval ordering preferred the stale value. The fix stores
the LLM extractor's correction marker on the fact row (encrypted, ordering
metadata only) and enforces at read time that a validated correction - same
fail-closed bar as supersession linking - sorts ahead of the fact it
corrects. Stored importance is never mutated, no status flips, and no
supersession rows are written while the gate is OFF.

Runs against real PostgreSQL (pgserver fixture) with real encryption and the
real migration files, like test_fact_supersession_db.py.
"""

import json
import uuid
from datetime import datetime, timedelta

import pytest

pgserver = pytest.importorskip("pgserver")
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
MSG3 = str(uuid.uuid4())

USERS_STUB = "CREATE TABLE IF NOT EXISTS users (id UUID PRIMARY KEY DEFAULT gen_random_uuid());"
MIGRATIONS = [
    "migrations/011_memory_facts.sql",
    "migrations/013_fact_supersession.sql",
    "migrations/015_fact_corrects_marker.sql",
]


@pytest.fixture(scope="module")
def pg(tmp_path_factory):
    server = pgserver.get_server(tmp_path_factory.mktemp("pg"))
    yield server
    server.cleanup()


@pytest.fixture()
def db(pg, monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", pg.get_uri())
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", Fernet.generate_key().decode())
    # The live production state: durable supersession stays OFF.
    monkeypatch.setattr(settings, "MEMORY_SUPERSESSION_ENABLED", False)
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


def _seed(engine, text_value, *, importance, age_hours=2, category="goal", extractor="llm", corrects=None):
    fact_id = str(uuid.uuid4())
    created = datetime(2026, 10, 31, 6, 0, 0) - timedelta(hours=age_hours)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO memory_facts (id, user_id, fact, fact_key, category, importance,
                                          extractor, created_at, corrects)
                VALUES (:id, :user_id, :fact, :fact_key, :category, :importance,
                        :extractor, :created_at, :corrects)
                """
            ),
            {
                "id": fact_id,
                "user_id": USER,
                "fact": encrypt_text(text_value),
                "fact_key": fact_key(text_value),
                "category": category,
                "importance": importance,
                "extractor": extractor,
                "created_at": created,
                "corrects": encrypt_text(json.dumps(corrects)) if corrects else None,
            },
        )
    return fact_id


def _rows(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).mappings().all()


def _correction():
    return ScoredFact(NEW_TEXT, "goal", 0.8, 0.0, "llm", dict(CORRECTS))


def _contents(facts):
    return [fact["content"] for fact in facts]


def test_correction_outranks_stale_despite_lower_importance(db):
    _seed(db, OLD_TEXT, importance=0.9)
    store = FactStore()
    store.upsert_facts(USER, [_correction()], MSG2)

    top = store.list_top(USER, 8)
    assert _contents(top)[:2] == [NEW_TEXT, OLD_TEXT]
    core = store.list_core(USER)
    assert _contents(core)[:2] == [NEW_TEXT, OLD_TEXT]

    # Ordering-only: stored state is untouched.
    new_row = _rows(db, "SELECT importance, status FROM memory_facts WHERE fact_key = :k", k=fact_key(NEW_TEXT))[0]
    assert new_row["importance"] == 0.8  # no importance mutation
    assert new_row["status"] == "active"
    old_row = _rows(db, "SELECT status FROM memory_facts WHERE fact_key = :k", k=fact_key(OLD_TEXT))[0]
    assert old_row["status"] == "active"
    audits = _rows(db, "SELECT id FROM memory_fact_supersessions WHERE user_id = :u", u=USER)
    assert audits == []  # gate OFF: no durable supersession writes

    # The marker is stored encrypted on the fact row, not as plaintext.
    raw = _rows(db, "SELECT corrects FROM memory_facts WHERE fact_key = :k", k=fact_key(NEW_TEXT))[0]["corrects"]
    assert isinstance(raw, str)
    assert "January 11" not in raw
    assert json.loads(decrypt_text(raw))["new_value"] == "January 11"


def test_stale_remention_cannot_reoutrank(db):
    _seed(db, OLD_TEXT, importance=0.9)
    store = FactStore()
    store.upsert_facts(USER, [_correction()], MSG2)
    # The stale fact is mentioned again: mention_count 2 and an importance
    # bump. Under a pure importance floor this tie would flip back.
    store.upsert_facts(USER, [ScoredFact(OLD_TEXT, "goal", 0.9, 0.0, "llm")], MSG3)

    old_row = _rows(db, "SELECT mention_count, importance FROM memory_facts WHERE fact_key = :k", k=fact_key(OLD_TEXT))[0]
    assert old_row["mention_count"] == 2
    assert old_row["importance"] > 0.9

    assert _contents(store.list_top(USER, 8))[0] == NEW_TEXT


def test_no_marker_keeps_importance_order(db):
    _seed(db, OLD_TEXT, importance=0.9)
    store = FactStore()
    store.upsert_facts(USER, [ScoredFact(NEW_TEXT, "goal", 0.8, 0.0, "llm")], MSG2)

    assert _contents(store.list_top(USER, 8))[:2] == [OLD_TEXT, NEW_TEXT]


def test_ambiguous_marker_no_reorder(db):
    _seed(db, OLD_TEXT, importance=0.9)
    _seed(db, OLD_TEXT + " with Arjun", importance=0.9)
    store = FactStore()
    store.upsert_facts(USER, [_correction()], MSG2)

    contents = _contents(store.list_top(USER, 8))
    assert contents[-1] == NEW_TEXT  # both stale matches still outrank it


def test_manual_target_never_reordered(db):
    _seed(db, OLD_TEXT, importance=0.9, extractor="manual")
    store = FactStore()
    store.upsert_facts(USER, [_correction()], MSG2)

    assert _contents(store.list_top(USER, 8))[:2] == [OLD_TEXT, NEW_TEXT]


def test_query_resort_keeps_correction_first(db):
    _seed(db, OLD_TEXT, importance=0.9)
    store = FactStore()
    store.upsert_facts(USER, [_correction()], MSG2)

    # The query matches the stale fact better, so relevance + importance
    # alone would rank it first; correction ordering must still win.
    top = store.list_top(USER, 8, query="triathlon December 14")
    assert top[0]["content"] == NEW_TEXT
    # Public shape unchanged: no internal keys leak to callers.
    assert set(top[0].keys()) == {"id", "content", "memory_tier", "importance_score", "created_at", "last_seen_at"}
CHAIN_A = "Training for a triathlon in Goa on December 14"
CHAIN_B = "Training for a triathlon in Goa on January 11"
CHAIN_C = "Training for a triathlon in Goa on March 5"


def _marker(old_value, new_value):
    return {
        "entity": "Goa triathlon",
        "attribute": "date",
        "old_value": old_value,
        "new_value": new_value,
        "polarity_old": "neutral",
        "polarity_new": "neutral",
    }


def test_correction_outside_page_still_constrains(db):
    # 25 fillers at 0.85 push the 0.8 correction outside the n*3=24 page.
    # Containment must still pull it in and rank it ahead of the stale fact.
    for i in range(25):
        _seed(db, f"Filler note number {i} about ordinary weekday routines", importance=0.85, age_hours=3 + i)
    _seed(db, OLD_TEXT, importance=0.9)
    store = FactStore()
    store.upsert_facts(USER, [_correction()], MSG2)

    top = store.list_top(USER, 8)
    assert top[0]["content"] == NEW_TEXT
    assert top[1]["content"] == OLD_TEXT


def test_correction_below_core_minimum_still_constrains_core_list(db):
    # Containment deliberately widens membership for marker-bearing facts: a
    # validated correction is a current-truth claim, so it joins the core
    # list even below the 0.8 tier minimum.
    _seed(db, OLD_TEXT, importance=0.9)
    store = FactStore()
    store.upsert_facts(USER, [ScoredFact(NEW_TEXT, "goal", 0.7, 0.0, "llm", dict(CORRECTS))], MSG2)

    core = _contents(store.list_core(USER))
    assert core[:2] == [NEW_TEXT, OLD_TEXT]


def test_reversal_chain_newest_correction_wins(db):
    _seed(db, CHAIN_A, importance=0.9, age_hours=4)
    store = FactStore()
    store.upsert_facts(USER, [ScoredFact(CHAIN_B, "goal", 0.85, 0.0, "llm", _marker("December 14", "January 11"))], MSG2)
    store.upsert_facts(USER, [ScoredFact(CHAIN_C, "goal", 0.8, 0.0, "llm", _marker("January 11", "March 5"))], MSG3)

    assert _contents(store.list_top(USER, 8))[:3] == [CHAIN_C, CHAIN_B, CHAIN_A]


def test_cycle_attempt_only_newer_constraint_applies(db):
    # Adversarial/buggy extractor: both facts carry markers targeting each
    # other. The older fact's marker cannot target a newer candidate (age
    # check), so only the newer fact's constraint applies; nothing loops,
    # nothing is dropped.
    _seed(db, OLD_TEXT, importance=0.9, age_hours=4, corrects=_marker("January 11", "December 14"))
    store = FactStore()
    store.upsert_facts(USER, [_correction()], MSG2)

    assert _contents(store.list_top(USER, 8))[:2] == [NEW_TEXT, OLD_TEXT]
    rows = _rows(db, "SELECT id FROM memory_facts WHERE user_id = :u AND status = 'active'", u=USER)
    assert len(rows) == 2


def test_bogus_marker_without_match_changes_nothing(db):
    # Extractor emitted a marker for a quoted/third-party statement whose
    # entity and old value match no active fact: ordering is untouched.
    _seed(db, OLD_TEXT, importance=0.9)
    store = FactStore()
    bogus = ScoredFact(
        "My friend Ravi is moving to Delhi in March",
        "life_event",
        0.8,
        0.0,
        "llm",
        {
            "entity": "Ravi move",
            "attribute": "city",
            "old_value": "Mumbai",
            "new_value": "Delhi",
            "polarity_old": "neutral",
            "polarity_new": "neutral",
        },
    )
    store.upsert_facts(USER, [bogus], MSG2)

    assert _contents(store.list_top(USER, 8))[:2] == [OLD_TEXT, "My friend Ravi is moving to Delhi in March"]


def test_ordering_flag_off_restores_importance_order(db, monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_CORRECTION_ORDERING_ENABLED", False)
    _seed(db, OLD_TEXT, importance=0.9)
    store = FactStore()
    store.upsert_facts(USER, [_correction()], MSG2)

    assert _contents(store.list_top(USER, 8))[:2] == [OLD_TEXT, NEW_TEXT]
