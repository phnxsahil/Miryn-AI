# Backend Test Guide

## Structure

- `tests/` contains pytest suites mirroring the backend package layout.
- Fixture modules live in `tests/conftest.py` (create as needed).
- Integration tests that hit the running API should live under `tests/integration/`.

## Running tests

```bash
cd miryn/backend
pytest
```

Set required environment variables (see `backend/.env.example`) or export a test-safe `.env` before running.

## Writing new tests

- Prefer fast unit tests that isolate services (mock Supabase/Redis/LLM clients).
- For database-dependent tests, use the Dockerized Postgres+pgvector from `docker-compose.yml` or an in-memory SQLite fallback.
- Assert both success paths and common failure cases (e.g., validation errors, permission checks).
- When adding new routes, include health checks under `tests/test_<feature>.py`.

## Conventions

- Use descriptive test names: `test_<function>_<condition>_<expected>()`.
- Keep fixtures idempotent and clean up external resources.
- Snapshot or golden-file tests should store artifacts under `tests/fixtures/`.
