"""Offline fictional replay of explicit-correction supersession mechanics.

Replays fictional correction conversations through the REAL chain - stub LLM
JSON -> score_message_llm parse/validation -> upsert -> link_explicit_corrections
against a real PostgreSQL database (pgserver) with the real migrations (011 +
013) and real Fernet encryption - and checks that fail-closed behavior holds.

BOUNDARY: the stub LLM returns canned marker payloads, so this validates the
mechanics only. It says NOTHING about whether the real model emits reliable
correction markers; MEMORY_SUPERSESSION_ENABLED must stay off until that is
validated with real LLM calls.

Run from miryn/backend:  python3 evals/correction_supersession/run_correction_replay.py
Requires: pgserver (pip install pgserver), app settings env (SECRET_KEY etc.).
"""
import asyncio
import json
import sys
import uuid
from pathlib import Path

import pgserver
from cryptography.fernet import Fernet
from sqlalchemy import text

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from app.config import settings  # noqa: E402
from app.core import database  # noqa: E402
from app.core.database import get_sql_session  # noqa: E402
from app.core.encryption import decrypt_text  # noqa: E402
from app.services.fact_store import FactStore  # noqa: E402
from app.services.importance import ScoredFact, score_message_llm  # noqa: E402

USERS_STUB = "CREATE TABLE IF NOT EXISTS users (id UUID PRIMARY KEY DEFAULT gen_random_uuid());"
MIGRATIONS = ["migrations/011_memory_facts.sql", "migrations/013_fact_supersession.sql"]


class StubLLM:
    """Returns a canned extraction payload; stands in for the real model."""

    def __init__(self, payload):
        self.payload = payload

    async def generate(self, prompt, max_tokens=400):
        return json.dumps(self.payload)

    def parse_json_response(self, response):
        return json.loads(response)


def apply_schema():
    with database._db.engine.begin() as conn:
        conn.execute(text(USERS_STUB))
        for migration in MIGRATIONS:
            for statement in (BACKEND / migration).read_text().split(";"):
                if statement.strip():
                    conn.execute(text(statement))


def fact_states(user_id):
    with get_sql_session() as session:
        rows = session.execute(
            text("SELECT fact, status FROM memory_facts WHERE user_id = :u"),
            {"u": user_id},
        ).mappings().all()
    active, superseded = set(), set()
    for row in rows:
        content = (decrypt_text(row["fact"]) or "").strip()
        (active if row["status"] == "active" else superseded).add(content) \
            if row["status"] in ("active", "superseded") else None
    return active, superseded


def main():
    scenarios = json.loads((BACKEND / "evals/correction_supersession/scenarios.json").read_text())["scenarios"]
    failures = 0
    for scenario in scenarios:
        server = pgserver.get_server(Path("./pgdata_" + uuid.uuid4().hex[:8]).resolve())
        settings.DATABASE_URL = server.get_uri()
        settings.ENCRYPTION_KEY = Fernet.generate_key().decode()
        settings.MEMORY_SUPERSESSION_ENABLED = True
        database._db = database.Database()
        apply_schema()
        user_id = str(uuid.uuid4())
        with get_sql_session() as session:
            session.execute(text("INSERT INTO users (id) VALUES (:id)"), {"id": user_id})
        store = FactStore()
        for setup in scenario.get("setup_facts", []):
            store.upsert_facts(user_id, [ScoredFact(
                setup["fact"], setup["category"], setup["importance"],
                setup["emotional_weight"], setup["extractor"],
            )], str(uuid.uuid4()))
        for message in scenario["messages"]:
            stub = StubLLM(message["llm_response"])
            facts = asyncio.run(score_message_llm(stub, message["text"]))
            store.upsert_facts(user_id, facts, str(uuid.uuid4()))
            store.link_explicit_corrections(user_id, facts, str(uuid.uuid4()))
        active, superseded = fact_states(user_id)
        server.cleanup()
        expected_active = set(scenario["expected_active"])
        expected_superseded = set(scenario["expected_superseded"])
        ok = active == expected_active and superseded == expected_superseded
        failures += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  {scenario['name']}")
        if not ok:
            print(f"  expected active={sorted(expected_active)} superseded={sorted(expected_superseded)}")
            print(f"  actual   active={sorted(active)} superseded={sorted(superseded)}")
    print(f"\n{len(scenarios) - failures}/{len(scenarios)} scenarios pass "
          "(mechanics only; real marker reliability unvalidated, gate stays off)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
