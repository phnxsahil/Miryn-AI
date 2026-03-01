# MIRYN AI — Standard Operating Procedure
> Version 1.0 | Based on full codebase audit | February 2026

---

## WHAT THIS DOCUMENT IS

This is the single source of truth for building, running, and extending Miryn. Every section maps directly to actual code. Nothing here is aspirational — it reflects what exists and what is missing.

Read this before writing a single line of code.

---

## PART 1 — ARCHITECTURE OVERVIEW

### Stack

| Layer | Technology | Location |
|---|---|---|
| Backend | FastAPI (Python) | `miryn/backend/` |
| Frontend | Next.js 14 (App Router) | `miryn/frontend/` |
| Database | PostgreSQL + pgvector | via `DATABASE_URL` or Supabase |
| Cache / Events | Redis | `REDIS_URL` |
| Background Jobs | Celery | `workers/celery_app.py` |
| LLM | OpenAI / Anthropic / Gemini / Vertex | `services/llm_service.py` |
| Embeddings | Configurable (384-dim vectors) | `core/embeddings.py` |
| Encryption | AES at rest for memory content | `core/encryption.py` |
| Auth | JWT (HS256, 7-day expiry) | `core/security.py` |

### How a message flows through the system

```
User sends message
       ↓
POST /chat/  (api/chat.py)
       ↓
Validate conversation ownership
       ↓
Auto-create conversation if none exists
       ↓
ConversationOrchestrator.handle_message()  (services/orchestrator.py)
       ↓
├── IdentityEngine.get_identity()          → Load user's current identity version
├── MemoryLayer.retrieve_context()         → Hybrid recall (semantic + temporal + importance)
├── MemoryLayer.store_conversation()       → Persist user message (tiered: transient/episodic/core)
├── ReflectionEngine.detect_contradictions() → Check new message vs existing beliefs
├── LLMService.chat()                      → Build system prompt + context → call LLM
├── MemoryLayer.store_conversation()       → Persist assistant message
└── analyze_reflection.delay()            → Queue Celery background task
       ↓
Return ChatResponse (response, conversation_id, insights, conflicts)
       ↓
Background: reflection_worker processes conversation
       ↓  [THIS STEP IS CURRENTLY BROKEN — see Critical Fixes]
IdentityEngine.update_identity()          → Write beliefs/emotions/patterns back
```

### Memory Architecture (3 tiers)

```
TRANSIENT  → Redis, 2hr TTL, short/ephemeral messages, not embedded
EPISODIC   → PostgreSQL, 7-day retrieval window, embedded at 384 dims
CORE       → PostgreSQL, permanent, high importance score (≥0.8), semantic search
```

Retrieval strategy on every message: semantic search (cosine similarity > 0.7) + temporal search (last 7 days) + importance search (score ≥ 0.7) → hybrid score merge → top 5 injected into context.

### Identity Architecture (versioned)

Every identity change creates a **new row** in `identities` table with `version + 1`. Never mutates. This means you always have full history. The identity is hydrated from 5 sub-tables: `identity_beliefs`, `identity_open_loops`, `identity_patterns`, `identity_emotions`, `identity_conflicts`.

---

## PART 2 — LOCAL DEVELOPMENT SETUP

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL with pgvector extension
- Redis
- Docker (optional, for compose)

### Backend setup

```bash
cd miryn/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # Fill in values — see ENV VARS section
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend setup

```bash
cd miryn/frontend
npm install
cp .env.example .env.local         # Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

### Docker (full stack)

```bash
cd miryn
docker compose up -d --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

### Run database migrations

```bash
psql $DATABASE_URL -f miryn/backend/migrations/001_init.sql
```

---

## PART 3 — ENVIRONMENT VARIABLES

All vars live in `miryn/backend/.env`. Required ones will crash the app on startup if missing.

### Required (app will not start without these)

```env
SECRET_KEY=<random 32+ char string>
DATABASE_URL=postgresql://user:pass@host:5432/miryn
```

### LLM Provider (pick one set)

```env
LLM_PROVIDER=openai                    # openai | anthropic | gemini | vertex
OPENAI_API_KEY=sk-...

# OR
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# OR
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-1.5-flash-001

# OR
LLM_PROVIDER=vertex
VERTEX_PROJECT_ID=...
VERTEX_MODEL=google/gemini-2.0-flash-lite-001
```

### Optional but important

```env
REDIS_URL=redis://localhost:6379
FRONTEND_URL=http://localhost:3000
ENCRYPTION_KEY=<32-byte base64 key>   # Enable at-rest encryption for memory
SUPABASE_URL=...                       # Only if using Supabase instead of direct Postgres
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
TOOL_SANDBOX_URL=...                   # Remote Python sandbox URL (optional)
```

### Security defaults (change for production)

```env
ACCESS_TOKEN_EXPIRE_MINUTES=10080      # 7 days
RATE_LIMIT_PER_MINUTE=60
LOGIN_ATTEMPT_LIMIT=5
LOGIN_ATTEMPT_WINDOW_SECONDS=900       # 15 minutes
AUDIT_RETENTION_DAYS=90
AUDIT_STORE_PII=false
```

---

## PART 4 — API REFERENCE

Base URL: `http://localhost:8000` (dev) | your Railway/Render URL (prod)

All protected endpoints require: `Authorization: Bearer <token>`

### Auth

| Method | Endpoint | Body | Returns |
|---|---|---|---|
| POST | `/auth/signup` | `{email, password}` | `{id, email}` |
| POST | `/auth/login` | `{email, password}` | `{access_token}` |

**Token storage:** Frontend stores in `localStorage` as `miryn_token`. Loaded by `api.loadToken()` on every page mount.

**Rate limiting:** Login has Redis-backed brute force guard. 5 attempts per 15 minutes per email/IP. Returns 429 after limit.

**Missing (build these):**
- `POST /auth/forgot-password` → send reset email
- `POST /auth/reset-password` → update hash with token
- `POST /auth/verify-email` → confirm email
- `POST /auth/refresh` → renew JWT silently
- `DELETE /account` → soft delete user + purge memories

### Chat

| Method | Endpoint | Body / Params | Returns |
|---|---|---|---|
| POST | `/chat/` | `{message, conversation_id?}` | `{response, conversation_id, insights?, conflicts?}` |
| GET | `/chat/history` | `?conversation_id=` | `[{id, role, content, created_at, ...}]` |
| GET | `/chat/events/stream` | `?token=` or `Authorization` header | SSE stream |

**Auto conversation creation:** If `conversation_id` is not provided, a new conversation is auto-created and the ID is returned. Frontend should save and reuse this ID.

**SSE stream events:**
- `reflection.ready` → `{type, payload: ConversationInsights}`
- `identity.conflict` → `{type, payload: [{statement, conflict_with, severity}]}`
- `notification.new` → `{type, payload: Notification}`

**Missing (build this):**
- `POST /chat/stream` → streaming token response (SSE chunks of the actual reply)

### Identity

| Method | Endpoint | Body | Returns |
|---|---|---|---|
| GET | `/identity/` | — | Full identity object |
| PATCH | `/identity/` | Partial identity fields | Updated identity |

**Identity object shape:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "version": 3,
  "state": "active",
  "traits": {"openness": 0.8, "reflectiveness": 0.7},
  "values": {"autonomy": 0.9, "honesty": 0.85},
  "beliefs": [{"topic": "...", "belief": "...", "confidence": 0.7}],
  "open_loops": [{"topic": "...", "status": "open", "importance": 2}],
  "patterns": [{"pattern_type": "...", "description": "...", "confidence": 0.6}],
  "emotions": [{"primary_emotion": "anxious", "intensity": 0.6, "secondary_emotions": []}],
  "conflicts": [{"statement": "...", "conflict_with": "...", "severity": 0.4}]
}
```

**Missing (build these):**
- `GET /identity/evolution` → paginated evolution log (what changed, when, why)
- `GET /memory` → categorized memory snapshot
- `DELETE /memory/:id` → soft-delete a specific memory

### Onboarding

| Method | Endpoint | Body | Returns |
|---|---|---|---|
| POST | `/onboarding/complete` | `{responses[], traits?, values?}` | `{status, identity}` |

**Current state:** Saves raw Q&A responses and calls `update_identity()` with provided traits/values. Does NOT load presets. Does NOT seed identity from responses automatically.

**What needs to change:** Accept a `preset` field, load from `config/presets.json`, write structured initial identity from preset config. See Preset Instructions file.

### Notifications

| Method | Endpoint | Returns |
|---|---|---|
| GET | `/notifications/` | `[{id, type, payload, status, created_at}]` |
| POST | `/notifications/read/:id` | 200 OK |

### Tools

| Method | Endpoint | Body | Returns |
|---|---|---|---|
| POST | `/tools/generate` | `{intent, tool_type}` | Tool run object |
| GET | `/tools/pending` | — | `[ToolRun]` |
| POST | `/tools/approve` | `{tool_id}` | `{result: {output, error}}` |

---

## PART 5 — FRONTEND PAGES & COMPONENTS

### Route structure

```
app/
├── (auth)/
│   ├── login/page.tsx           → Login form → POST /auth/login → store token
│   └── signup/page.tsx          → Signup form → POST /auth/signup → redirect to onboarding
├── (app)/
│   ├── layout.tsx               → Protected layout, auth check, sidebar
│   ├── onboarding/page.tsx      → OnboardingFlow component
│   ├── chat/page.tsx            → ChatInterface component
│   └── identity/page.tsx        → IdentityDashboard component
└── page.tsx                     → Root redirect (→ chat if authed, → login if not)
```

### Component inventory

**Chat components** (`components/Chat/`)
- `ChatInterface.tsx` — Master chat component. Manages: messages state, SSE connection, loading state, conversation ID, insights, conflicts, pending tools, notifications. Sends messages via `api.sendMessage()`. Full SSE listener wired to `reflection.ready`, `identity.conflict`, `notification.new`.
- `InputBox.tsx` — Auto-resize textarea. Enter=send, Shift+Enter=newline. Send button disabled while loading.
- `MessageBubble.tsx` — Renders user/assistant/system messages. Style varies by role.
- `InsightsPanel.tsx` — Renders `ConversationInsights` after reflection completes via SSE.
- `NotificationsPanel.tsx` — Renders notification list. markRead via `api.markNotificationRead()`.
- `ToolPanel.tsx` — Lists pending tool runs. Approve button calls `api.approveTool()`.

**Identity components** (`components/Identity/`)
- `IdentityDashboard.tsx` — Full identity view. Renders: stats (beliefs/loops/patterns/emotions counts), traits (pills), values (pills), beliefs (with confidence meter), open loops (with priority), patterns (with confidence meter), emotions (with intensity meter), conflicts, privacy vault note.
- `IdentityCard.tsx` — Individual identity card (used inside dashboard).

**Onboarding** (`components/Onboarding/`)
- `OnboardingFlow.tsx` — **Currently: 4 flat text questions, no steps, no preset selection, no progress indicator.** Submits all answers at once. No redirect after completion.

### What's missing in frontend

**Pages that need to be created:**
- `app/(app)/memory/page.tsx` — Memory snapshot page
- `app/(app)/settings/page.tsx` — Account settings + danger zone

**Components that need to be created:**
- `components/Identity/EvolutionTimeline.tsx` — Render identity_evolution_log as human-readable events
- `components/Memory/MemoryCard.tsx` — Single memory item with forget button
- `components/Memory/MemorySnapshot.tsx` — Categorized memory list
- `components/Chat/StreamingMessage.tsx` — Token-by-token streaming render

**Components that need redesign:**
- `OnboardingFlow.tsx` — Needs 5-step wizard with preset selection (see Design Spec below)
- `IdentityDashboard.tsx` — Needs evolution timeline section, needs trait values shown as numbers not just labels

### Design system (actual current tokens)

From `tailwind.config.ts` and class patterns in components:

```
Background:    bg-void (very dark, near-black with purple tint)
Text primary:  text-white
Text muted:    text-secondary (white/50-60 opacity)
Accent:        bg-accent (the purple — used for buttons)
Cards:         bg-black/30 or bg-black/40 with border-white/10
Radius:        rounded-2xl (cards), rounded-full (pills, buttons)
Typography:    font-serif for headings (Miryn headers), font-light for display
Tracking:      tracking-[0.2em] to tracking-[0.35em] for all labels (uppercase)
Borders:       border-white/10 everywhere
Meters:        bg-gradient-to-r from-amber-400/80 via-amber-300/70 to-white/60
```

---

## PART 6 — CRITICAL FIXES (do these first)

### Fix 1 — Wire reflection results to identity (MOST IMPORTANT)

**File:** `miryn/backend/app/workers/reflection_worker.py`

The `analyze_reflection` Celery task calls `ReflectionEngine.analyze_conversation()` which returns:
```python
{
  "entities": [...],
  "emotions": {"primary_emotion": "...", "intensity": 0.7, "secondary_emotions": [...]},
  "topics": [...],
  "patterns": {"topic_co_occurrences": [...], "temporal_emotional_patterns": [...]},
  "insights": "..."
}
```

**These results are currently discarded.** Add after `analyze_conversation()`:

```python
identity_engine = IdentityEngine()

# Write emotions
if result["emotions"].get("primary_emotion"):
    identity_engine.update_identity(user_id, {
        "emotions": [result["emotions"]]
    })

# Write patterns
if result["patterns"].get("topic_co_occurrences"):
    identity_engine.update_identity(user_id, {
        "patterns": [
            {"pattern_type": "topic_co_occurrence", 
             "description": p["pattern"], 
             "confidence": min(p["frequency"] / 10, 1.0)}
            for p in result["patterns"]["topic_co_occurrences"]
        ]
    })

# Write open loops from unresolved topics
for topic in result["topics"]:
    identity_engine.track_open_loop(user_id, topic, importance=1)
```

### Fix 2 — Add streaming endpoint

**File:** `miryn/backend/app/api/chat.py`

Add a `POST /chat/stream` endpoint that uses `StreamingResponse` with SSE. The `LLMService` needs a `stream_chat()` async generator method added alongside the existing `chat()` method.

### Fix 3 — Fix detect_conflicts() stub

**File:** `miryn/backend/app/services/identity_engine.py` lines 198-210

Currently returns `[]` always. Should call `self.reflection.detect_contradictions()` — but `IdentityEngine` doesn't hold a reference to `ReflectionEngine`. Options: inject `ReflectionEngine` into `IdentityEngine.__init__()`, or move the call to the orchestrator (already calls both separately — wire them together).

### Fix 4 — Add evolution log writes

**File:** `miryn/backend/app/services/identity_engine.py` — `update_identity()` method

Add a migration (`002_evolution_log.sql`) for the table, then after every successful identity insert:
```python
session.execute(text("""
    INSERT INTO identity_evolution_log 
    (user_id, identity_id, field_changed, old_value, new_value, trigger_type, created_at)
    VALUES (:user_id, :identity_id, :field, :old, :new, :trigger, NOW())
"""), {...})
```

### Fix 5 — Expand onboarding to use presets

**File:** `miryn/backend/app/api/onboarding.py`

Add `preset: str` to `OnboardingCompleteRequest` schema. On `complete_onboarding()`, load `config/presets.json`, find the preset by ID, and seed the identity with preset's `initial_traits`, `values`, `memory_weights`, and write initial beliefs from the user's seed belief answer.

---

## PART 7 — DESIGN SPEC (every screen)

### Screen 1 — Login (`/login`)

**State:** email input, password input, submit button, error message, link to signup  
**Flow:** `api.login()` → store token via `api.setToken()` → redirect to `/onboarding` if no identity, `/chat` if identity exists  
**Design:** centered card on dark bg, Miryn logo above, no clutter. Single-column.

### Screen 2 — Signup (`/signup`)

**State:** email, password, confirm password, submit, error, link to login  
**Flow:** `api.signup()` → auto-login → redirect to `/onboarding`  
**Design:** same as login card

### Screen 3 — Onboarding (`/onboarding`) — NEEDS REBUILD

**Current state:** 4 flat textarea questions, no steps  
**Target state:** 5-step wizard

```
Step 1 — Welcome + Context
  Miryn introduces itself (short paragraph)
  Input: "What's your name?" + "In one sentence, what do you use AI for?"
  Progress: Step 1 of 5

Step 2 — Preset Selection
  Heading: "How should Miryn show up for you?"
  5 cards laid out in a grid:
    [The Thinker]    [The Companion]    [The Coach]
    [The Mirror]     [The Creative]
  Each card: title, 1-line description, example response snippet
  Selection: single-select with highlighted border on chosen card

Step 3 — Goals
  Heading: "What do you most want from Miryn?"
  Multi-select chips (not inputs):
    "Think through decisions"   "Creative work"
    "Emotional support"         "Accountability"
    "Learning"                  "Just someone to talk to"

Step 4 — Communication Style
  Heading: "How do you like to be spoken to?"
  Two sliders or toggle pairs:
    Direct ←————→ Gentle
    Brief  ←————→ Expansive

Step 5 — Seed Belief (optional)
  Heading: "Tell Miryn one thing you believe strongly."
  Subheading: "Optional — but the more you give, the faster Miryn understands you."
  Single textarea, placeholder: "I believe that..."
  Skip option clearly visible

Nav: Back / Next buttons. Progress bar at top. Completion → animated transition into /chat
```

### Screen 4 — Chat (`/chat`)

**Current state:** Working. Messages render correctly. SSE connected. Tool and notification panels exist.

**Missing:**
- Conversation list sidebar (left panel, list of past conversations with auto-titles)
- Streaming token render (currently shows full response after delay)
- Copy button on MessageBubble hover
- New conversation button (Cmd+K or visible button)
- Empty state for zero messages (first time user sees this screen)

**Empty state design:** Center of screen, Miryn logo, tagline "A quiet room for honest reflection.", a prompt suggestion like "Start by telling me about your week." — subtle, not gamified.

**Layout target:**
```
┌──────────────────────────────────────────────────┐
│  Sidebar          │  Header (Miryn + subtitle)   │
│  ─────────        │  ─────────────────────────── │
│  [+] New chat     │  Message history              │
│                   │  ...                          │
│  Past chats:      │  ...                          │
│  > Chat title 1   │  [MessageBubble user]         │
│  > Chat title 2   │  [MessageBubble assistant]    │
│  > Chat title 3   │                               │
│                   │  ─────────────────────────── │
│                   │  [InputBox]                   │
└──────────────────────────────────────────────────┘
```

### Screen 5 — Identity Dashboard (`/identity`)

**Current state:** Renders all identity fields. Stats row exists. Traits/values as pills. Beliefs/loops with meters.

**Missing:**
- Evolution timeline section — "What Miryn has noticed" — chronological log of identity changes with human-readable descriptions
- Trait values displayed as numbers alongside pills (currently just shows key, not value)
- Active open loops shown with time since opened
- "Last updated" timestamps on each section

**Add evolution timeline section at bottom:**
```
┌─────────────────────────────────────────────────┐
│  WHAT MIRYN HAS NOTICED                         │
│  ───────────────────────                        │
│  Feb 14 — After your conversation about work,   │
│           Miryn updated your Openness to 0.82   │
│                                                  │
│  Feb 12 — Miryn noticed you often discuss        │
│           creativity and autonomy together       │
│                                                  │
│  Feb 10 — A new belief was recorded: "Growth    │
│           requires discomfort"                   │
└─────────────────────────────────────────────────┘
```

### Screen 6 — Memory (`/memory`) — NEEDS CREATION

**Route:** `app/(app)/memory/page.tsx`

**Sections:**
```
Facts About You
  Cards: [Work in product management] [Based in Delhi] [Have a sister]
  Each card: content text, date recorded, importance dot (●●● scale)
  [Forget this] button on hover

Emotional Patterns
  Cards showing recurring emotional themes
  Example: "You tend to feel anxious on Sunday evenings"

People In Your Life
  Cards per mentioned person
  Example: [Marcus — Friend — Last mentioned Feb 14]

Goals & Plans
  Active goals with status chips
  Example: [Learn to cook — Active] [Finish the side project — Active]

[Export my data] button at bottom (JSON download)
```

### Screen 7 — Settings (`/settings`) — NEEDS CREATION

**Sections:**
- Account: email display, change password
- Notifications: toggle for check-in reminders, weekly digest
- Privacy: memory encryption status, data retention
- Danger Zone: Delete account (requires typing "DELETE" to confirm)

---

## PART 8 — DATABASE MIGRATIONS NEEDED

### 002_evolution_log.sql (create this file)

```sql
CREATE TABLE IF NOT EXISTS identity_evolution_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    identity_id UUID NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
    field_changed VARCHAR(100) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    trigger_type VARCHAR(100),   -- 'reflection', 'onboarding', 'manual'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS evolution_log_user_id_idx 
    ON identity_evolution_log(user_id, created_at DESC);

-- Add missing indexes on messages for performance
CREATE INDEX IF NOT EXISTS messages_conversation_created_idx 
    ON messages(conversation_id, created_at);

-- Add preset tracking to identities
ALTER TABLE identities 
    ADD COLUMN IF NOT EXISTS preset VARCHAR(50);

ALTER TABLE identities
    ADD COLUMN IF NOT EXISTS memory_weights JSONB DEFAULT '{"facts": 0.33, "emotions": 0.33, "goals": 0.34}';

-- Add soft delete and email verify to users
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT false;
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false;
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP;
```

---

## PART 9 — CELERY WORKERS

Workers live in `miryn/backend/app/workers/`:

| Worker file | Task | Triggered by |
|---|---|---|
| `reflection_worker.py` | `analyze_reflection` — runs full reflection pipeline | `orchestrator.py` after each message |
| `memory_worker.py` | Memory processing tasks | TBD |
| `outreach_worker.py` | Sends check-in notifications | `outreach_scheduler.py` scan |

### Running workers locally

```bash
cd miryn/backend
celery -A app.workers.celery_app worker --loglevel=info
```

### Running the outreach scheduler

```bash
# Run once (manual trigger)
python -c "from app.services.outreach_scheduler import OutreachScheduler; OutreachScheduler().scan()"

# In production: add a cron job or Celery beat schedule to run daily
```

---

## PART 10 — TESTING

### Existing tests

```
tests/test_encryption.py     — AES encrypt/decrypt round trip
tests/test_health.py         — GET /health returns 200
tests/test_tool_sandbox.py   — Python sandbox blocklist + execution
```

### Tests that need to be written

```
tests/test_reflection_engine.py
  - test entity extraction returns list
  - test emotion extraction returns dict with primary_emotion
  - test contradiction detection with conflicting beliefs
  - test pattern detection with mocked history

tests/test_memory_layer.py
  - test store + retrieve round trip
  - test tier selection logic (transient vs episodic vs core)
  - test hybrid scoring produces ordered results
  - test cache invalidation on store

tests/test_identity_engine.py
  - test version increments on every update
  - test merge logic (dict merge for traits/values)
  - test belief recording upserts correctly
  - test open loop tracking

tests/test_orchestrator.py
  - test full message flow with mocked LLM
  - test fallback response on LLM failure
  - test conflict detection integration
```

Run tests:
```bash
cd miryn/backend
pytest tests/ -v
```

---

## PART 11 — DEPLOYMENT

### Current setup
- Frontend: Vercel (`miryn-ai.vercel.app`)
- Backend: not yet deployed to prod (local only)

### Recommended production stack
- Backend: Railway (handles FastAPI, has managed PostgreSQL, easy env vars)
- Database: Railway PostgreSQL with pgvector extension enabled
- Redis: Railway Redis add-on
- Celery workers: Railway worker process (separate from web process)
- Frontend: Vercel (already there, keep it)

### Environment vars for production
All vars from Part 3, plus:
```env
FRONTEND_URL=https://miryn-ai.vercel.app
BACKEND_URL=https://your-railway-app.railway.app
```

### Vercel → Railway CORS
The `FRONTEND_URL` env var on the backend is what controls CORS. Set it to your exact Vercel URL including `https://`.

---

## PART 12 — KNOWN ISSUES & TECH DEBT

| Issue | Severity | Location |
|---|---|---|
| `detect_conflicts()` returns `[]` always | High | `identity_engine.py:198` |
| Reflection results never written to identity | Critical | `reflection_worker.py` |
| No streaming — chat blocks until full response | High | `api/chat.py`, `llm_service.py` |
| Onboarding doesn't load presets | High | `api/onboarding.py` |
| No evolution log table or writes | High | missing migration + `identity_engine.py` |
| No password reset / email verify | High | `api/auth.py` |
| No JWT refresh endpoint | Medium | `api/auth.py` |
| Traits displayed as pills not scored values | Medium | `IdentityDashboard.tsx` |
| OnboardingFlow has no steps or preset selection | High | `OnboardingFlow.tsx` |
| Memory dedup not implemented | Medium | `memory_layer.py` |
| No token count guard on context window | Medium | `llm_service.py` |
| `health` endpoint doesn't check DB or Redis | Low | `main.py` |
| Spots counter on waitlist is hardcoded | Medium | waitlist site |

---

## PART 13 — GLOSSARY

| Term | Meaning |
|---|---|
| Identity version | An immutable snapshot of the user's full identity. Increments on every meaningful change. |
| Open loop | A topic or question mentioned in conversation that has no recorded resolution yet. |
| Reflection pipeline | The background process that extracts entities, emotions, beliefs from a conversation and writes them back to the identity. |
| Memory tier | Classification of a memory: transient (Redis, short-lived), episodic (PostgreSQL, recent), core (PostgreSQL, permanent, high importance). |
| Preset | The initial personality configuration chosen during onboarding that seeds the identity. |
| Hybrid retrieval | Memory recall strategy combining semantic similarity + temporal recency + importance score. |
| Evolution log | Append-only audit trail of every identity field change with timestamp and trigger reason. |
| Conflict | A detected contradiction between a new statement and an existing recorded belief. |

---

*End of SOP v1.0 — Update this document whenever the architecture changes.*
