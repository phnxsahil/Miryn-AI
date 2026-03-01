# GEMINI.md - Miryn AI Development Guide

This document is the foundational mandate for Gemini CLI. It combines instructions from `SOP.md` and `AGENTS.MD`.

## Core Mandates & Rules
- **Security:** Never use raw SQL strings without parameterized values.
- **Data Integrity:** 
    - All identity changes MUST go through `IdentityEngine.update_identity()`.
    - All memory writes MUST go through `MemoryLayer.store_conversation()`.
- **Architecture:** 
    - Every new endpoint needs a corresponding schema in `miryn/backend/app/schemas/`.
    - Frontend API calls MUST use `miryn/frontend/lib/api.ts`.
- **Protected Files:** Do not modify these without explicit instruction:
    - `miryn/backend/app/core/encryption.py`
    - `miryn/backend/app/core/security.py`
    - `miryn/backend/migrations/001_init.sql`

## Technical Stack
- **Backend:** FastAPI (Python), PostgreSQL + pgvector, Redis, Celery.
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS.
- **Memory:** 3-tier (Transient/Redis, Episodic/Postgres, Core/Postgres).
- **Identity:** Versioned, immutable snapshots.

## Import Patterns
- **Backend:** `from app.services.identity_engine import IdentityEngine`, `from app.core.database import get_db, has_sql, get_sql_session`
- **Frontend:** `import { api } from "@/lib/api"`, `import type { Identity } from "@/lib/types"`

## Frontend Standards
- **Mobile First:** All new UI components MUST be mobile-responsive by default.
- **Dynamic Viewport:** Use `h-[100dvh]` for full-height application containers to ensure they work correctly across all mobile browsers and account for the address bar/keyboard.
- **Responsive Grids:** Prefer `grid-cols-1 md:grid-cols-X` for section layouts to ensure they stack correctly on small screens.
- **Interactive Elements:** Buttons and inputs should have sufficient padding (min `py-2.5` or `py-3`) for touch targets on mobile.
- **Typography:** Scale headings responsibly (e.g., `text-2xl md:text-4xl`) and use `leading-relaxed` for body text to improve readability on small screens.

## Local Development & Sandbox Setup
### Backend (`miryn/backend/`)
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
cp .env.example .env
```
### Frontend (`miryn/frontend/`)
```bash
npm install
cp .env.example .env.local
```

## Critical Fixes (Priority Order)
1. **Reflection Pipeline:** `reflection_worker.py` discards results; must write to identity.
2. **Streaming:** Add `POST /chat/stream` and `LLMService.stream_chat()`.
3. **Onboarding:** Load presets from `config/presets.json` (needs creation).
4. **Identity Conflicts:** Implement `detect_conflicts()` stub in `identity_engine.py`.
5. **Evolution Log:** Create `identity_evolution_log` table and implement writes.

## Testing Standards
- Always run `pytest tests/ -v` in `miryn/backend/` after changes.
- Ensure new endpoints have unit tests in `tests/`.

---
*Derived from SOP.md and AGENTS.MD (v1.0)*
