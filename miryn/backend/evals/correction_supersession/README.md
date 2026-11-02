# Correction supersession replay (offline, fictional)

Replays fictional correction conversations through the real chain:

stub LLM JSON -> `score_message_llm` parse/validation -> `upsert_facts` ->
`link_explicit_corrections` against a real PostgreSQL database (pgserver) with
the real migrations (011 + 013) and real Fernet encryption.

## Boundary

The stub LLM returns canned marker payloads, so this validates **mechanics
only**: marker validation, fail-closed supersede selection, the transaction and
audit-row behavior. It says **nothing** about whether the real model emits
reliable correction markers. `MEMORY_SUPERSESSION_ENABLED` must stay off until
real-LLM marker reliability is validated with real provider calls. While the
gate is off, explicit durable correction (hiding a superseded fact) is
unsupported in production; this replay is a prerequisite mechanics check, not
that validation.

## Scenarios (all fictional people and events)

- valid date correction supersedes the old fact
- preference correction with a polarity flip supersedes
- preference correction WITHOUT a polarity flip fails closed (both stay active)
- marker missing `old_value` is dropped at parse time
- identical old/new value is dropped at parse time
- manual memories are never superseded
- multiple eligible candidates fail closed

## Run

```
pip install pgserver
SECRET_KEY=... ENCRYPTION_KEY=... DATABASE_URL=sqlite:///./x.db REDIS_URL=redis://127.0.0.1:9 \
  python3 evals/correction_supersession/run_correction_replay.py
```

Exit code is non-zero if any scenario fails.
