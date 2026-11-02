"""DB-integration replay for fictional scenarios (deterministic, offline).

Complements run_answer_replay.py: instead of hand-feeding fact lists into
_format_context, this seeds each scenario's facts through the REAL write path
(FactStore.upsert_facts: importance-threshold filtering, Fernet encryption,
conflict upsert) into a real PostgreSQL database (pgserver test fixture, real
migrations 011 + 013), then retrieves through the REAL chat-path read
(FactStore.list_top(user, 8, probe) exactly as api/chat.py calls it) and
assembles the REAL system prompt + context via LLMService.

What this proves (per scenario):
- the seeded facts survive the write-path threshold and land in the context
  the model would see (context_must_include)
- the system prompt carries the behaviour rules the answer must follow
  (prompt_must_include), as before
- for correction scenarios, with the supersession gate ON, the corrected fact
  is hidden from retrieval (gate-on check)

What this does NOT prove:
- that answers follow the rules (needs gated real-model runs)
- that corrections currently win: with the gate OFF (production default),
  conflicting facts BOTH surface, ordered importance-first on a lexical miss.
  That current ordering is reported as INFO, never asserted as correct
  behaviour - the gate is the intended durable-correction mechanism and it is
  deliberately fail-closed until real-LLM marker reliability is validated.

Requires the test dependency pgserver (not part of the CI-parity suite).
Run from miryn/backend:  python3 evals/answer_replay/run_context_replay.py
"""
import json
import sys
import tempfile
import uuid
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

import pgserver  # noqa: E402
from cryptography.fernet import Fernet  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.config import settings  # noqa: E402
from app.core import database  # noqa: E402
from app.services.fact_store import FactStore  # noqa: E402
from app.services.importance import ScoredFact, fact_key  # noqa: E402
from app.services.llm_service import LLMService  # noqa: E402

USERS_STUB = "CREATE TABLE IF NOT EXISTS users (id UUID PRIMARY KEY DEFAULT gen_random_uuid());"
MIGRATIONS = ["migrations/011_memory_facts.sql", "migrations/013_fact_supersession.sql", "migrations/015_fact_corrects_marker.sql"]
THRESHOLD_NOTE = "write path keeps facts with importance >= IMPORTANCE_CORE_THRESHOLD * 0.8"


def fresh_db(pg):
    settings.DATABASE_URL = pg.get_uri()
    settings.ENCRYPTION_KEY = Fernet.generate_key().decode()
    database._db = database.Database()
    with database._db.engine.begin() as conn:
        conn.execute(text(USERS_STUB))
        for migration in MIGRATIONS:
            for statement in open(BACKEND / migration).read().split(";"):
                if statement.strip():
                    conn.execute(text(statement))
    return database._db.engine


def seed_scenario(engine, scenario):
    user_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO users (id) VALUES (:id)"), {"id": user_id})
    store = FactStore()
    scored = []
    for fact in scenario.get("facts") or []:
        scored.append(
            ScoredFact(
                fact["content"],
                fact.get("category", "goal"),
                fact.get("importance_score", 0.9),
                fact.get("emotional_weight", 0.0),
                fact.get("extractor", "llm"),
                dict(fact["corrects"]) if fact.get("corrects") else None,
            )
        )
    if scored:
        store.upsert_facts(user_id, scored, str(uuid.uuid4()))
        # Backdate created_at to the scenario timestamps so correction
        # chronology (strictly-older candidates) matches how the facts would
        # have been written over time.
        with engine.begin() as conn:
            for fact in scenario.get("facts") or []:
                if fact.get("created_at"):
                    conn.execute(
                        text(
                            "UPDATE memory_facts SET created_at = :created, last_seen_at = :created "
                            "WHERE user_id = :user_id AND fact_key = :fact_key"
                        ),
                        {
                            "created": fact["created_at"],
                            "user_id": user_id,
                            "fact_key": fact_key(fact["content"]),
                        },
                    )
    return user_id, store, scored


def assemble(svc, scenario, facts):
    identity = dict(scenario.get("identity") or {})
    identity.setdefault("preset", "companion")
    system = svc._build_system_prompt(identity)
    context = svc._format_context({"known_facts": facts, "memories": scenario.get("memories") or []})
    return system, context


def run(pg):
    scenarios = json.loads((BACKEND / "evals/answer_replay/scenarios.json").read_text())["scenarios"]
    svc = LLMService()
    failures = 0
    for scenario in scenarios:
        name = scenario["name"]
        # --- Gate OFF (production default): write path -> chat-path read ---
        settings.MEMORY_SUPERSESSION_ENABLED = False
        engine = fresh_db(pg)
        user_id, store, _ = seed_scenario(engine, scenario)
        facts = store.list_top(user_id, 8, scenario.get("probe") or "")
        system, context = assemble(svc, scenario, facts)
        combined = system + "\n" + context
        missing_prompt = [s for s in scenario.get("prompt_must_include", []) if s not in combined]
        seeded_contents = [f["content"] for f in scenario.get("facts") or []]
        visible = [f["content"] for f in facts]
        missing_ctx = [c for c in seeded_contents if not any(c in v for v in visible)]
        dated = [f for f in scenario.get("facts") or [] if f.get("created_at")]
        missing_dates = [f"[recorded {f['created_at'][:10]}]" for f in dated
                         if f"[recorded {f['created_at'][:10]}]" not in context]
        status = "PASS" if not missing_prompt and not missing_ctx and not missing_dates else "FAIL"
        failures += 0 if status == "PASS" else 1
        print(f"{status}  {name} (gate OFF: write+retrieval path, {THRESHOLD_NOTE})")
        for s in missing_prompt:
            print(f"  missing in prompt: {s!r}")
        for c in missing_ctx:
            print(f"  missing in retrieved context: {c!r}")
        for d in missing_dates:
            print(f"  missing statement date in context: {d}")
        if len(visible) > 1:
            print(f"  INFO retrieval order (importance-first on lexical miss): {visible}")

        # --- Gate ON (intended semantics): explicit correction hides the old fact ---
        corrections = [f for f in scenario.get("facts") or [] if f.get("corrects")]
        if corrections:
            settings.MEMORY_SUPERSESSION_ENABLED = True
            engine = fresh_db(pg)
            user_id, store, scored = seed_scenario(engine, scenario)
            new_facts = [sf for sf in scored if sf.corrects]
            links = store.link_explicit_corrections(user_id, new_facts, str(uuid.uuid4()))
            facts = store.list_top(user_id, 8, scenario.get("probe") or "")
            visible = [f["content"] for f in facts]
            hidden_ok = all(not any(f["content"] in v for v in visible)
                            for f in scenario["facts"]
                            if not f.get("corrects") and any(f["content"] != nf.text for nf in new_facts))
            new_visible = all(any(nf.text in v for v in visible) for nf in new_facts)
            linked = len(links) == len(new_facts)
            status = "PASS" if hidden_ok and new_visible and linked else "FAIL"
            failures += 0 if status == "PASS" else 1
            print(f"{status}  {name} (gate ON: correction link hides corrected fact)")
            if not linked:
                print(f"  expected {len(new_facts)} correction link(s), got {len(links)}")
            if not hidden_ok:
                print(f"  corrected fact still visible: {visible}")
            if not new_visible:
                print(f"  correcting fact missing: {visible}")
    total = sum(1 + (1 if any(f.get("corrects") for f in s.get("facts") or []) else 0)
                for s in scenarios)
    print(f"\n{total - failures}/{total} context-replay checks pass "
          "(deterministic; answer-level still needs gated real model runs)")
    return failures


def main():
    with tempfile.TemporaryDirectory() as tmp:
        pg = pgserver.get_server(Path(tmp))
        try:
            failures = run(pg)
        finally:
            pg.cleanup()
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
