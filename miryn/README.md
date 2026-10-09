# Miryn

Miryn is a context-aware AI companion with persistent memory, reflective insights, and an identity system that evolves over time.

## Stack

- Backend: FastAPI + Supabase (Postgres + pgvector) + Redis
- Frontend: Next.js 14 + TypeScript + Tailwind
- Infra: Docker Compose

## Project Structure

```
miryn/
  backend/
  frontend/
  shared/
  docker-compose.yml
  README.md
```

## Setup

### 1) Configure environment variables

Docker Compose uses `miryn/.env`:

- Update `miryn/.env` values
- Required for local dev: `DATABASE_URL`, `SECRET_KEY`
- Optional: Supabase keys if using Supabase instead of local Postgres
- Redis is provided via the `redis` service in `docker-compose.yml`. Set
  `REDIS_URL` (default `redis://redis:6379/0`) or supply `REDIS_HOST` /
  `REDIS_PORT` + optional `REDIS_PASSWORD`. For password-protected Redis use
  `redis://:password@host:port/db` and keep the password in your secret store.

Backend (non-docker):

- Copy `backend/.env.example` to `backend/.env`
- Fill in:
  - `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` (if using Supabase)
  - or `DATABASE_URL` for local Postgres
  - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
  - `SECRET_KEY` — generate at least a 32-byte secret and never commit it.
    Example commands:
    - Python: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
    - OpenSSL: `openssl rand -base64 32`
    Rotate production secrets regularly and store them in your secrets manager.

Frontend:

- Copy `frontend/.env.example` to `frontend/.env`
- Set `NEXT_PUBLIC_API_URL` if different

### 2) Apply database schema

- Fresh Docker volume: `docker compose -f miryn/docker-compose.yml up -d postgres` applies `backend/migrations/001..011` automatically (only when the volume is empty).
- Existing volume: initdb does not run again, so apply new migrations manually. All migrations are idempotent, so re-running is safe:

  ```sh
  docker compose -f miryn/docker-compose.yml exec -T postgres sh -c 'for f in /docker-entrypoint-initdb.d/*.sql; do echo "== $f"; psql -U postgres -d miryn -v ON_ERROR_STOP=1 -q -f "$f" || exit 1; done'
  ```

  On PowerShell, run each file separately if the shell loop is awkward, for example:

  ```sh
  docker compose -f miryn/docker-compose.yml exec -T postgres psql -U postgres -d miryn -f /docker-entrypoint-initdb.d/011_memory_facts.sql
  ```

  Run files `002` through `011` in order. If the database user or name differs from `postgres`/`miryn`, use `POSTGRES_USER` and `POSTGRES_DB` from `.env`.
- Supabase: run the files in `backend/migrations` in order in the SQL editor, starting with `001`.
- SQLite demo only: `python init_db.py` (uses `backend/sqlite/000_sqlite_init.sql`).

### 3) Run with Docker Compose

From `miryn/`:

```
docker compose up -d --build
```

Backend will be available at `http://localhost:8000` and frontend at `http://localhost:3000`.

## API Endpoints

- `POST /auth/signup`
- `POST /auth/login`
- `POST /chat/`
- `GET /chat/history`
- `GET /identity/`
- `PATCH /identity/`
- `POST /onboarding/complete`

## Notes

- The backend can use Supabase or local Postgres via `DATABASE_URL`.
- `postgres` in `docker-compose.yml` is included for local development.
- The `match_messages` SQL function is required for semantic search.
- Rate limiting and audit logging are enabled.

## Manual Testing Checklist

Backend:
- POST /auth/signup creates user
- POST /auth/login returns token
- POST /chat sends message and returns response
- GET /chat/history returns conversation
- Hybrid retrieval returns relevant memories
- Identity versioning creates new versions
- Reflection pipeline extracts entities/emotions

Frontend:
- Landing page loads
- Signup/login flow works
- Onboarding flow completes
- Chat interface sends/receives messages
- Identity dashboard loads
