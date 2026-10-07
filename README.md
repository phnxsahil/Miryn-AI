# Miryn

**An AI companion that actually remembers you, and builds a versioned model of who you are over time.**

Most chatbots forget everything when the tab closes. Miryn keeps a tiered long-term memory of your conversations, retrieves what's relevant on every message, and maintains an identity profile (traits, beliefs, open loops, emotional patterns) that updates as you talk.

[Join the waitlist (live)](https://miryn-ai.vercel.app)

> **Screenshot:** _add chat + identity dashboard screenshots here_
> **Architecture diagram:** _optional, add one image of the flow below_

## What it does

- **Remembers across sessions.** Messages are embedded and stored as vectors in Postgres (pgvector), then recalled by meaning, not keywords.
- **Retrieves with a hybrid score.** Semantic similarity, recency and importance are combined, not just nearest-neighbour.
- **Reflects in the background.** Celery workers analyse conversations for emotions, topic patterns and open loops, and write them back to your identity.
- **Keeps an identity that evolves.** Traits, values, beliefs, open loops and conflicts are stored per user, and every change is logged so you can see how the profile moved.

## The memory / RAG pipeline

```
user message
   |
   +--> embed (Gemini embeddings, deterministic hash fallback) --> store
   |        tier chosen per message: transient | episodic | core
   |
   +--> retrieve_context(query)
          |-- semantic : pgvector cosine search (messages.embedding, 384-dim)
          |-- temporal : last 7 days
          |-- important: importance >= 0.7
          |-- transient: short-lived items from Redis (2h TTL)
          v
   hybrid score = 0.5 * semantic + 0.3 * recency + 0.2 * importance
          v
   top-k memories (cached in Redis for 1h) --> LLM prompt --> reply
```

- **Three tiers.** `transient` (short or ephemeral, kept in Redis), `episodic` (default), `core` (importance >= 0.8). Tier can also be set explicitly.
- **Provider-agnostic LLM layer.** Switch with `LLM_PROVIDER`: `openai`, `anthropic`, `gemini` or `vertex`.
- **Optional learned re-ranker.** `memory_ranker.py` can re-rank memories with an XGBoost model over recency, emotional intensity, entity overlap and identity alignment, and falls back to importance score when the model is unavailable.
- **Privacy basics.** Message content is encrypted at rest (`ENCRYPTION_KEY`), with rate limiting and audit logging on the API.

## Identity engine

Per-user identity stored in Postgres: traits and values, `identity_beliefs`, `identity_open_loops`, `identity_patterns`, `identity_emotions` and `identity_conflicts`, plus an evolution log for each change. The reflection worker (`app/workers/reflection_worker.py`) feeds it after conversations.

## Tech stack

| Layer | Tools |
|---|---|
| Frontend | Next.js 14, React, TypeScript, Tailwind, NextAuth, Sentry |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Data | PostgreSQL + pgvector, Redis |
| Background jobs | Celery (worker + beat) |
| ML | sentence-transformers, XGBoost, scikit-learn |
| LLMs | OpenAI, Anthropic, Gemini, Vertex AI (switchable) |
| Infra | Docker Compose, GitHub Actions |

## Repo layout

```
miryn/
  backend/     FastAPI app: app/api, app/services, app/core, app/workers, migrations/
  frontend/    Next.js app
  shared/      shared types (Python + TypeScript)
  docker-compose.yml
```

## Quickstart (Docker)

You need Docker and at least one LLM key.

```bash
git clone https://github.com/phnxsahil/Miryn-AI.git
cd Miryn-AI/miryn

cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# fill in: an LLM key + LLM_PROVIDER, SECRET_KEY, ENCRYPTION_KEY,
# and DATABASE_URL pointing at the compose Postgres (user/password/db default to postgres/postgres/miryn)

docker compose up -d --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (FastAPI docs at `/docs`)

The compose file starts the backend, frontend, Celery worker and beat, Redis and Postgres with pgvector. SQL files in `backend/migrations/` are loaded on first database start.

## Local development

```bash
# backend
cd miryn/backend
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend
cd miryn/frontend
npm install
npm run dev
```

Backend tests: `cd miryn/backend && SECRET_KEY=test pytest -q`

## API overview

`/auth` (signup, login), `/chat`, `/identity`, `/onboarding`, `/memory`, `/notifications`, `/import`, `/llm`, `/tools`, plus analytics endpoints. Full interactive docs at `/docs` when the backend is running.

## Status

Alpha. The product is collecting waitlist signups at [miryn-ai.vercel.app](https://miryn-ai.vercel.app). The frontend still needs polish and I'm iterating on it.

## Author

Built by [Sahil Sharma](https://sharmasahil.me).
