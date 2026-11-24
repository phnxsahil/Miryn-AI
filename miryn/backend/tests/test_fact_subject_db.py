"""Subject/source provenance for supersession: seeded-DB and fake-extractor tests.

A model's subject claim is never proof. A link needs both facts stored as
subject 'user' plus trusted source messages (server-supplied id, owner's own
user message, text containing the corrected value).
"""
import asyncio
import uuid
from datetime import datetime, timedelta

import pgserver
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import text

from app.config import settings
from app.core import database
from app.core.encryption import encrypt_text
from app.services.fact_store import FactStore, subject_params
from app.services.importance import ScoredFact, fact_key, score_message_llm

OLD_TEXT = "Training for a triathlon in Goa on December 14"
NEW_TEXT = "Training for a triathlon in Goa on January 11"
CORRECTS = {"entity": "Goa triathlon", "attribute": "date", "old_value": "December 14",
            "new_value": "January 11", "polarity_old": "neutral", "polarity_new": "neutral"}
USER = str(uuid.uuid4())
OTHER_USER = str(uuid.uuid4())
CONV = str(uuid.uuid4())
OTHER_CONV = str(uuid.uuid4())
OLD_MSG = str(uuid.uuid4())
NEW_MSG = str(uuid.uuid4())

USERS_STUB = "CREATE TABLE IF NOT EXISTS users (id UUID PRIMARY KEY DEFAULT gen_random_uuid());"
CONV_STUB = "CREATE TABLE IF NOT EXISTS conversations (id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id));"
MSG_STUB = ("CREATE TABLE IF NOT EXISTS messages (id UUID PRIMARY KEY, conversation_id UUID NOT NULL REFERENCES conversations(id), "
            "user_id UUID NOT NULL REFERENCES users(id), role VARCHAR(20) NOT NULL, content TEXT, content_encrypted TEXT);")
MIGRATIONS = ["migrations/011_memory_facts.sql", "migrations/013_fact_supersession.sql",
              "migrations/015_fact_corrects_marker.sql", "migrations/016_fact_subject.sql"]


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
    monkeypatch.setattr(settings, "MEMORY_SUBJECT_ENABLED", True)
    database._db = database.Database()
    with database._db.engine.begin() as conn:
        conn.execute(text(USERS_STUB))
        for uid in (USER, OTHER_USER):
            conn.execute(text("INSERT INTO users (id) VALUES (:id)"), {"id": uid})
        conn.execute(text(CONV_STUB))
        conn.execute(text(MSG_STUB))
        conn.execute(text("INSERT INTO conversations (id, user_id) VALUES (:c, :u)"), {"c": CONV, "u": USER})
        conn.execute(text("INSERT INTO conversations (id, user_id) VALUES (:c, :u)"), {"c": OTHER_CONV, "u": OTHER_USER})
        for migration in MIGRATIONS:
            for statement in open(migration).read().split(";"):
                if statement.strip():
                    conn.execute(text(statement))
    yield database._db.engine
    with database._db.engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS memory_fact_supersessions, memory_facts, messages, conversations, users CASCADE"))
    database._db.engine = None
    database._db.SessionLocal = None


def _msg(engine, mid, content, *, user=USER, conv=CONV, role="user", encrypted=False):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO messages (id, conversation_id, user_id, role, content, content_encrypted) "
                 "VALUES (:id, :c, :u, :r, :content, :enc)"),
            {"id": mid, "c": conv, "u": user, "r": role,
             "content": None if encrypted else content, "enc": encrypt_text(content) if encrypted else None},
        )


def _seed(engine, text_value, *, subject="user", source=OLD_MSG, extractor="llm", age_hours=2):
    fid = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO memory_facts (id, user_id, fact, fact_key, category, importance, extractor, created_at, subject, source_message_id) "
                 "VALUES (:id, :u, :f, :k, 'goal', 0.9, :x, :t, :s, :src)"),
            {"id": fid, "u": USER, "f": encrypt_text(text_value), "k": fact_key(text_value), "x": extractor,
             "t": datetime(2026, 10, 31, 6) - timedelta(hours=age_hours), "s": subject, "src": source},
        )
    return fid


def _rows(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).mappings().all()


def _status(engine, fid):
    return _rows(engine, "SELECT status FROM memory_facts WHERE id=:i", i=fid)[0]["status"]


def _run_link(subject="user", source=NEW_MSG):
    store = FactStore()
    fact = ScoredFact(NEW_TEXT, "goal", 0.9, 0.0, "llm", dict(CORRECTS), subject)
    store.upsert_facts(USER, [fact], source)
    return store.link_explicit_corrections(USER, [fact], source)


def _happy_messages(engine):
    _msg(engine, OLD_MSG, "I am training for a triathlon in Goa on December 14")
    _msg(engine, NEW_MSG, "Actually the triathlon is on January 11 not December 14", encrypted=True)


def test_verified_user_to_user_link_is_made(db):
    _happy_messages(db)
    old = _seed(db, OLD_TEXT)
    links = _run_link()
    assert len(links) == 1 and links[0]["old_fact_id"] == old
    assert _status(db, old) == "superseded"


def test_legacy_unknown_row_is_never_superseded(db):
    _happy_messages(db)
    old = _seed(db, OLD_TEXT, subject="unknown", source=None)
    assert _run_link() == []
    assert _status(db, old) == "active"


def test_model_user_claim_with_invented_source_id_is_not_proof(db):
    _msg(db, OLD_MSG, "I am training for a triathlon in Goa on December 14")  # no stored message for NEW_MSG
    old = _seed(db, OLD_TEXT)
    assert _run_link() == []
    assert _status(db, old) == "active"


def test_new_source_from_another_owner_is_rejected(db):
    _msg(db, OLD_MSG, "I am training for a triathlon in Goa on December 14")
    _msg(db, NEW_MSG, "Actually the triathlon is on January 11", user=OTHER_USER, conv=OTHER_CONV)
    old = _seed(db, OLD_TEXT)
    assert _run_link() == []
    assert _status(db, old) == "active"


def test_old_source_from_another_owner_is_rejected(db):
    _msg(db, OLD_MSG, "I am training for a triathlon in Goa on December 14", user=OTHER_USER, conv=OTHER_CONV)
    _msg(db, NEW_MSG, "Actually the triathlon is on January 11")
    old = _seed(db, OLD_TEXT)
    assert _run_link() == []
    assert _status(db, old) == "active"


def test_assistant_message_is_not_a_source(db):
    _msg(db, OLD_MSG, "I am training for a triathlon in Goa on December 14")
    _msg(db, NEW_MSG, "Actually the triathlon is on January 11", role="assistant")
    old = _seed(db, OLD_TEXT)
    assert _run_link() == []
    assert _status(db, old) == "active"


def test_source_text_must_contain_the_corrected_value(db):
    _msg(db, OLD_MSG, "I am training for a triathlon in Goa on December 14")
    _msg(db, NEW_MSG, "Thanks, that is helpful")
    old = _seed(db, OLD_TEXT)
    assert _run_link() == []
    assert _status(db, old) == "active"


def test_other_subject_never_links(db):
    _happy_messages(db)
    old = _seed(db, OLD_TEXT)
    assert _run_link(subject="other") == []
    assert _status(db, old) == "active"


def test_user_claim_without_source_is_stored_unknown_and_never_links(db):
    _happy_messages(db)
    old = _seed(db, OLD_TEXT)
    store = FactStore()
    fact = ScoredFact(NEW_TEXT, "goal", 0.9, 0.0, "llm", dict(CORRECTS), "user")
    store.upsert_facts(USER, [fact], None)
    assert _rows(db, "SELECT subject FROM memory_facts WHERE fact_key=:k", k=fact_key(NEW_TEXT))[0]["subject"] == "unknown"
    assert store.link_explicit_corrections(USER, [fact], None) == []
    assert _status(db, old) == "active"


def test_unknown_matching_fact_still_blocks_a_link_as_ambiguity(db):
    _happy_messages(db)
    old = _seed(db, OLD_TEXT)
    other = _seed(db, "The Goa triathlon happens December 14", subject="unknown", source=None, age_hours=5)
    assert _run_link() == []
    assert _status(db, old) == "active" and _status(db, other) == "active"


def test_same_source_message_for_old_and_new_is_rejected(db):
    _msg(db, NEW_MSG, "Actually the triathlon is on January 11 not December 14")
    old = _seed(db, OLD_TEXT, source=NEW_MSG)
    assert _run_link() == []
    assert _status(db, old) == "active"


def test_subject_merge_rules_on_conflict(db):
    store = FactStore()
    t = "Works at Acme as an analyst"
    store.upsert_facts(USER, [ScoredFact(t, "work_career", 0.9, 0, "llm", None, "user")], NEW_MSG)
    store.upsert_facts(USER, [ScoredFact(t, "work_career", 0.9, 0, "heuristic", None, "unknown")], NEW_MSG)
    get = lambda: _rows(db, "SELECT subject FROM memory_facts WHERE fact_key=:k", k=fact_key(t))[0]["subject"]
    assert get() == "user"  # unknown does not erase a known subject
    store.upsert_facts(USER, [ScoredFact(t, "work_career", 0.9, 0, "llm", None, "other")], NEW_MSG)
    assert get() == "unknown"  # disagreement collapses to unknown


def test_flag_off_does_not_touch_subject_column(db, monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_SUBJECT_ENABLED", False)
    store = FactStore()
    store.upsert_facts(USER, [ScoredFact("Lives in Pune now", "identity", 0.9, 0, "llm", None, "user")], NEW_MSG)
    assert _rows(db, "SELECT subject FROM memory_facts WHERE fact_key=:k", k=fact_key("Lives in Pune now"))[0]["subject"] == "unknown"


# ---- extraction parsing with fake model output (no network)

class FakeLLM:
    def __init__(self, payload):
        self.payload = payload

    async def generate(self, prompt, max_tokens=400):
        return self.payload

    @staticmethod
    def parse_json_response(response):
        import json
        return json.loads(response)


def _extract(items):
    import json
    return asyncio.run(score_message_llm(FakeLLM(json.dumps({"facts": items})), "msg"))


def test_extractor_subject_values_are_normalised():
    facts = _extract([
        {"fact": "Lives in Pune", "category": "identity", "importance": 0.9, "subject": "user"},
        {"fact": "Sister lives in Delhi", "category": "relationship", "importance": 0.8, "subject": "OTHER"},
        {"fact": "Likes tea a lot", "category": "preference", "importance": 0.6, "subject": "me"},
    ])
    assert [f.subject for f in facts] == ["user", "other", "unknown"]
    missing = _extract([{"fact": "Has a cat named Momo", "category": "identity", "importance": 0.7}])
    assert missing[0].subject == "unknown"


def test_extractor_supplied_source_ids_are_ignored():
    facts = _extract([{"fact": "Lives in Pune", "category": "identity", "importance": 0.9,
                       "subject": "user", "source_message_id": "11111111-1111-1111-1111-111111111111"}])
    assert not hasattr(facts[0], "source_message_id")


def test_subject_params_downgrades_user_without_source():
    f = ScoredFact("x", "goal", 0.9, 0, "llm", None, "user")
    assert subject_params(f, None)["subject"] == "unknown"
    assert subject_params(f, "m1")["subject"] == "user"
