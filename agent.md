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

## Current broken things (fix these in order)
1. reflection_worker.py discards analyze_conversation() results — never writes to identity
2. No streaming endpoint exists — LLMService has no stream_chat() method
3. Onboarding doesn't load presets — config/presets.json doesn't exist yet
4. detect_conflicts() in identity_engine.py returns [] always (stub at line 198)
5. No identity_evolution_log table or writes exist

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

## After every backend change, check that
- The endpoint is registered in main.py if it's a new router
- The schema exists in app/schemas/ for any new request/response shape
- New migrations are additive only (ALTER TABLE ADD COLUMN IF NOT EXISTS)
