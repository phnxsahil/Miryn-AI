# Miryn AI — Agent Instructions

## Project structure
- Backend: miryn/backend/ (FastAPI, Python)
- Frontend: miryn/frontend/ (Next.js 14, TypeScript)
- Migrations: miryn/backend/migrations/
- Config: miryn/backend/app/config/

## Stack
- PostgreSQL + pgvector (DATABASE_URL env var)
- Redis (REDIS_URL env var)
- Celery workers in miryn/backend/app/workers/
- LLM provider abstraction in miryn/backend/app/services/llm_service.py

## Critical rules
- Never use raw SQL strings without parameterized values
- All identity changes must go through IdentityEngine.update_identity() — never direct DB writes
- Memory writes always go through MemoryLayer.store_conversation() — never direct inserts
- Every new endpoint needs a corresponding schema in miryn/backend/app/schemas/
- Frontend API calls always go through miryn/frontend/lib/api.ts — never direct fetch

## Previously-listed "broken things" — all 5 are FIXED (verified 2026-09-24)
Do not re-fix these; the code already does what this list used to claim was missing.
1. FIXED — `workers/reflection_worker.py` writes emotions, patterns and open loops via `IdentityEngine`.
2. FIXED — `LLMService.stream_chat()` exists (`services/llm_service.py`); `POST /chat/stream` serves SSE.
3. FIXED — `app/config/presets.json` exists and is loaded by `api/onboarding.py` and `llm_service._build_system_prompt()`.
4. FIXED — `detect_conflicts()` (`services/identity_engine.py`) delegates to `ReflectionEngine.detect_contradictions()`.
5. FIXED — `identity_evolution_log` table + writes exist (`migrations/002_evolution_log.sql`, `identity_engine._log_identity_evolution_sql`).

See the parent `../AGENTS.md` for the verified codebase map, and do not trust `SOP.md`, `GEMINI.md`, or `miryn_core.txt` for current state.

## Testing
- Run backend: cd miryn/backend && uvicorn app.main:app --reload
- Run frontend: cd miryn/frontend && npm run dev
- Run tests: cd miryn/backend && pytest tests/ -v

## Import patterns (always use these exact paths)
- Backend services: from app.services.identity_engine import IdentityEngine
- Backend DB: from app.core.database import get_db, has_sql, get_sql_session
- Frontend API: import { api } from "@/lib/api"
- Frontend types: import type { Identity } from "@/lib/types"

## Do not touch these files without being explicitly asked
- miryn/backend/app/core/encryption.py
- miryn/backend/app/core/security.py
- miryn/backend/migrations/001_init.sql

## Frontend UI Standards
- All UI components must be mobile-responsive by default.
- Use `h-[100dvh]` for full-height application containers.
- Use responsive grids (e.g., `grid-cols-1 md:grid-cols-2`) for layouts.
- Ensure buttons and inputs are touch-friendly (min `py-2.5`).

## After every backend change, check that
- The endpoint is registered in main.py if it's a new router
- The schema exists in app/schemas/ for any new request/response shape
- New migrations are additive only (ALTER TABLE ADD COLUMN IF NOT EXISTS)