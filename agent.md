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

## Current status (all core MVP features implemented)
1. ✅ Reflection worker writes emotions, patterns, and open loops to identity
2. ✅ Streaming endpoint exists (POST /chat/stream with SSE)
3. ✅ LLMService.stream_chat() implemented for all providers (OpenAI, Anthropic, Gemini, Vertex)
4. ✅ detect_conflicts() wired to ReflectionEngine.detect_contradictions()
5. ✅ identity_evolution_log table + writes in update_identity()
6. ✅ Onboarding loads presets from config/presets.json and seeds identity
7. ✅ Auth: signup, login, Google OAuth, refresh token, forgot/reset password, delete account, sessions
8. ✅ GET /identity/evolution — paginated evolution log
9. ✅ GET /memory/, DELETE /memory/:id, GET /memory/export — full memory API
10. ✅ Health endpoint checks DB and Redis connections
11. ✅ Frontend: 5-step onboarding wizard with preset selection
12. ✅ Frontend: Identity dashboard with evolution timeline + scored trait/value pills
13. ✅ Frontend: Memory page with forget button
14. ✅ Frontend: Settings page (account, notifications, privacy, appearance, danger zone)
15. ✅ Frontend: Conversation list sidebar with new chat button
16. ✅ Frontend: Chat empty state with tagline and prompt suggestion
17. ✅ Frontend: Streaming token-by-token message rendering

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
