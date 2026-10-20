# Miryn

Miryn is an AI companion that remembers the conversations that matter and builds a versioned model of the person it is talking with.

Instead of treating every chat as a blank slate, Miryn combines persistent memory, retrieval, reflection, and an evolving identity profile. The result is a prototype for conversations that can carry context forward without flattening a person into a single static persona.

**Product site:** [miryn-ai.vercel.app](https://miryn-ai.vercel.app)

## What the experience includes

- **Streaming conversations.** Responses arrive token by token through the FastAPI SSE endpoint.
- **Recalled context.** Relevant memories are retrieved from previous conversations before each reply.
- **An evolving identity.** Traits, values, beliefs, emotions, patterns, conflicts, and open loops are versioned per user.
- **Memory controls.** Users can inspect, export, and delete stored memories.
- **Background reflection.** Celery workers analyse conversations for emotional signals, recurring patterns, and unfinished threads.

## How it works

```mermaid
flowchart LR
    U[User message] --> O[Conversation orchestrator]
    O --> R[Hybrid memory retrieval]
    R --> L[LLM provider]
    L --> S[Streaming response]
    O --> M[Store conversation]
    M --> C[Celery reflection task]
    C --> I[Versioned identity]
    I --> R
```

The memory layer combines semantic similarity, recency, and importance. Memories are grouped into three tiers: short-lived `transient` context in Redis, default `episodic` memories, and higher-importance `core` memories. The retrieval path uses Postgres with pgvector and caches context in Redis.

After a conversation is stored, reflection can update identity evidence asynchronously. Identity changes go through the identity engine, which creates a new version and records the change in the evolution log.

The LLM service is provider-agnostic. Configure `LLM_PROVIDER` as `gemini`, `openai`, `anthropic`, or `vertex`; embedding and chat configuration remain in the backend environment.

## Technical shape

| Area | Implementation |
| --- | --- |
| Frontend | Next.js 14 App Router, React, TypeScript, Tailwind, Zustand |
| API | FastAPI, Pydantic, SQLAlchemy |
| Storage | PostgreSQL + pgvector, with a Supabase client path where configured |
| Cache and jobs | Redis, Celery worker, Celery beat |
| AI | Gemini, OpenAI, Anthropic, or Vertex through one service layer |
| Deployment | Docker Compose locally; Render blueprint for the API and Redis |

## Repository map

```text
miryn/
├── backend/
│   ├── app/api/       HTTP routers
│   ├── app/services/  memory, identity, reflection, and LLM logic
│   ├── app/workers/   Celery tasks
│   └── migrations/    PostgreSQL schema and pgvector setup
├── frontend/          Next.js application
└── docker-compose.yml Local backend, frontend, Redis, Postgres, and workers
```

## Run locally with Docker

Prerequisites: Docker Desktop and an API key for at least one supported LLM provider.

From the repository root:

```bash
cd miryn
cp .env.example .env
```

Edit `miryn/.env` and set at least:

```dotenv
DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/miryn
REDIS_URL=redis://redis:6379/0
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key
SECRET_KEY=generate-a-long-random-secret
ENCRYPTION_KEY=generate-a-fernet-key-or-use-a-long-random-value
```

For another provider, set its API key and change `LLM_PROVIDER`. Generate an application secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Start the stack from `miryn/`:

```bash
docker compose up -d --build
```

The services are then available at:

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API documentation: http://localhost:8000/docs
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

Postgres loads the SQL files in `backend/migrations/` only when the `postgres_data` volume is created for the first time. If you add migrations to an existing volume, apply them manually in order.

## Run without Docker

The backend expects Python 3.11 and a reachable PostgreSQL or Supabase database plus Redis.

```bash
# backend
cd miryn/backend
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend, in another terminal
cd miryn/frontend
npm install
npm run dev
```

For a non-Docker frontend, set `NEXT_PUBLIC_API_URL` in `miryn/frontend/.env` to the backend URL. Backend variables are documented in `miryn/backend/.env.example`.

## Checks

```bash
# backend tests (SQLite-compatible test configuration)
cd miryn/backend
SECRET_KEY=test pytest -q

# frontend lint and encoding checks
cd ../frontend
npm run verify
```

## Deployment note

`render.yaml` describes the current Render deployment shape: a Docker web service for the API and a managed Redis instance. The local Compose file also defines Postgres, the frontend, Celery worker, and Celery beat. Run the worker processes wherever background reflection is required; they are not separate services in the current Render blueprint.

Miryn is an alpha/demo project. The core memory, identity, streaming, reflection, and account flows are implemented, but the system is still being iterated and should be evaluated as a prototype rather than a production-ready service.

## Author

Built by [Sahil Sharma](https://sharmasahil.me).
