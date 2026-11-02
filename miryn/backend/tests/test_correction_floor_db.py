"""DB-backed tests for the correction importance floor (ordering-only).

Mirrors the live probe trace: a stale fact outranked its explicit correction
because the correction was stored with lower importance and the supersession
gate was OFF, so retrieval ordering preferred the stale value. The floor
lifts a validated correction's importance to the corrected fact's level
without any status change or supersession row.

Runs against real PostgreSQL (pgserver fixture) with real encryption and the
real migration files, like test_fact_supersession_db.py.
"""

import uuid
from datetime import datetime, timedelta

import pytest

pgserver = pytest.importorskip("pgserver")
from cryptography.fernet import Fernet
from sqlalchemy import text

from app.config import settings
from app.core import database
from app.services.fact_store import FactStore
from app.services.importance import ScoredFact

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


def _seed_stale(db):
    """Seed the stale fact as an already-active older row (live probe shape)."""
    with db.engine.begin() as conn:
        from app.core.encryption import encrypt_text
        conn.execute(
            text(
                """
                INSERT INTO memory_facts (user_id, fact, fact_key, category, importance, emotional_weight, extractor, created_at, last_seen_at)
                VALUES (:uid, :fact, :fkey, 'goal', 0.9, 0.5, 'llm', :ts, :ts)
                """
            ),
            {"uid": USER, "fact": encrypt_text(OLD_TEXT), "fkey": __import__("app.services.importance", fromlist=["fact_key"]).fact_key(OLD_TEXT),
             "ts": datetime(2026, 11, 2, 12, 0, 0)},
        )


def _facts(user_id):
    return FactStore()._list(user_id, 10)


def test_correction_floored_to_stale_importance(db):
    _seed_stale(db)
    correction = ScoredFact(NEW_TEXT, "goal", 0.8, 0.5, "llm", CORRECTS)
    FactStore().upsert_facts(USER, [correction], MSG2)
    facts = _facts(USER)
    texts = {f["content"]: f["importance_score"] for f in facts}
    assert texts[OLD_TEXT] == 0.9
    assert texts[NEW_TEXT] == 0.9  # floored to the stale fact's importance


def test_correction_ranks_first_in_list_top(db):
    _seed_stale(db)
    correction = ScoredFact(NEW_TEXT, "goal", 0.8, 0.5, "llm", CORRECTS)
    FactStore().upsert_facts(USER, [correction], MSG2)
    top = FactStore().list_top(USER, 8, "when is my race?")
    assert top[0]["content"] == NEW_TEXT


def test_gate_off_still_no_supersession(db):
    _seed_stale(db)
    correction = ScoredFact(NEW_TEXT, "goal", 0.8, 0.5, "llm", CORRECTS)
    FactStore().upsert_facts(USER, [correction], MSG2)
    FactStore().link_explicit_corrections(USER, [correction], MSG2)
    facts = _facts(USER)
    assert len(facts) == 2  # both active: fail-closed linking unchanged
    with db.engine.begin() as conn:
        rows = conn.execute(text("SELECT COUNT(*) AS n FROM memory_fact_supersessions")).mappings().one()
    assert rows["n"] == 0


def test_no_floor_without_marker(db):
    _seed_stale(db)
    other = ScoredFact("Enjoys morning runs along the river", "habit_change", 0.8, 0.3, "llm", None)
    FactStore().upsert_facts(USER, [other], MSG2)
    facts = _facts(USER)
    texts = {f["content"]: f["importance_score"] for f in facts}
    assert texts["Enjoys morning runs along the river"] == 0.8


def test_no_floor_on_non_matching_marker(db):
    _seed_stale(db)
    wrong = dict(CORRECTS, old_value="next year")
    correction = ScoredFact(NEW_TEXT, "goal", 0.8, 0.5, "llm", wrong)
    FactStore().upsert_facts(USER, [correction], MSG2)
    facts = _facts(USER)
    texts = {f["content"]: f["importance_score"] for f in facts}
    assert texts[NEW_TEXT] == 0.8  # old_value not in stale text: no match, no floor
