# Answer-level memory-behaviour replay (offline-first, fictional)

Builds the REAL system prompt and user context
(`LLMService._build_system_prompt` + `_format_context`) for fictional scenarios
and checks that the prompt carries what each behaviour rule needs
(`prompt_must_include`).

## Boundary

Prompt-level checks prove instructions and context are present, NOT that
answers follow them. `reply_must_include` / `reply_must_not_include` are
checked against a generated reply only with a real provider, which is GATED on
spend/billing grounding and not run by default.

## Run

```
SECRET_KEY=... ENCRYPTION_KEY=... DATABASE_URL=sqlite:///./x.db REDIS_URL=... \
  OPENAI_API_KEY=dummy LLM_PROVIDER=openai \
  python3 evals/answer_replay/run_answer_replay.py
```

Exit code is non-zero if any prompt check fails.

## DB-integration replay (run_context_replay.py)

`run_context_replay.py` goes one level deeper than prompt presence: it seeds
each scenario's facts through the REAL write path (`FactStore.upsert_facts`:
importance-threshold filtering, Fernet encryption, conflict upsert) into real
PostgreSQL (pgserver test fixture, real migrations 011 + 013), retrieves
through the REAL chat-path read (`FactStore.list_top(user, 8, probe)` exactly
as `api/chat.py` calls it), then assembles the same prompt/context.

Checks per scenario:
- gate OFF (production default): seeded facts survive the write path and land
  in the retrieved context; prompt rules still present.
- gate ON (correction scenarios): `link_explicit_corrections` hides the
  corrected fact from retrieval; the correcting fact stays visible.

Honest boundary: with the gate OFF, conflicting facts BOTH surface, ordered
importance-first on a lexical miss (reported as INFO, not asserted as
correct). Known facts reach the prompt as bare strings - `_format_context`
emits no per-fact timestamps or supersession metadata, so the prompt's
"most recent statement wins" rule can only draw on whatever chronology the
conversation itself carries (episodic memories do get `[ts]` prefixes), not
on fact metadata. Durable correction relies on the supersession gate, which
stays fail-closed until real-LLM marker reliability is validated.
Answer-level behaviour still needs gated real-model runs.

```
SECRET_KEY=... OPENAI_API_KEY=dummy LLM_PROVIDER=openai \
  python3 evals/answer_replay/run_context_replay.py
```
