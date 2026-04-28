Objective facts

1) Database tables: 15 tables in backend migrations (users, identities, identity_beliefs, identity_open_loops, identity_patterns, identity_emotions, identity_conflicts, conversations, messages, onboarding_responses, audit_logs, memory_summaries, tool_runs, notifications, identity_evolution_log). Supabase migration set defines 14 tables (missing identity_evolution_log).

2) Migrations: 10 SQL migration files total: 6 in miryn/backend/migrations and 4 in supabase/migrations.

3) Indexes: 19 CREATE INDEX statements in backend migrations (including 1 vector index). Primary keys: 15. Composite indexes: 2 explicit (messages_user_tier_idx, identity_evolution_log_user_created_idx) plus 1 composite unique constraint on identities(user_id, version). Vector index: 1 (messages_embedding_idx). Partial indexes: 0.

4) pgvector / embedding store: pgvector extension enabled and embedding vector(384) column with ivfflat index; SQLAlchemy Vector(384) used.

5) RPC functions / transactional DB operations: 1 SQL RPC function match_messages defined in migrations and called via Supabase RPC in MemoryLayer. Transactional DB operations: 50 get_sql_session() usage blocks in app code (includes reads and writes).

6) API routes / serverless functions: FastAPI routes = 36 (routers + root + health). Next.js API handlers = 3 (POST /api/demo-login, GET+POST /api/auth/[...nextauth]). Total = 39.

7) Background jobs / async workflows: 4 Celery tasks (memory.gc, memory.summarize, reflection.analyze, outreach.scan) + 2 FastAPI BackgroundTasks for imports = 6 queued workflows. Additionally, 3 in-process fire-and-forget async tasks in the orchestrator.

8) External integrations: 7 integrations: OpenAI, Anthropic, Google Gemini, Vertex AI, Supabase, Redis, Google OAuth.

9) Client-side derived computations: 14 explicit derived computations over state/data (filters, aggregates, computed metrics). Examples: notification count and stream aggregation in ChatInterface, assistant text paragraphing in MessageBubble, stats/key derivations in IdentityDashboard, onboarding progress and goal toggling in OnboardingFlow, memory snapshot empty-state and deletions in MemoryPage, preferences merging in SettingsPage.

10) Potential race-condition points: 9 identifiable non-atomic or concurrent write paths (create-then-update flows, delete-then-insert replaces, non-transactional fan-out).

11) Idempotency on write paths: No idempotency keys or dedupe tokens on write endpoints; retries are ad hoc (email uniqueness and identity insert retries only).

12) Pagination on memory/history queries: No pagination/cursor in /chat/history, /memory/export, or /memory/; fixed limits only in some queries.

13) Caching: Redis used for context cache, transient memory, rate limits, event streams, and import status.

Scores (1-10) with concrete justifications

Data integrity: 5/10
- Foreign keys and constraints are present in migrations.
- Identity evolution logging exists only in backend migrations (missing in Supabase set).
- Several writes are multi-step without a single transaction boundary.
- Identity sub-stores use delete-then-insert without guarding against partial failure.

Concurrency safety: 4/10
- Multiple non-atomic sequences (conversation create + message write + updated_at update).
- Background fire-and-forget writes run without coordination.
- Delete-then-insert replacements are race-prone.
- SELECT MAX(version) then insert creates a race window under concurrent writes.

Scalability: 5/10
- pgvector ivfflat index present.
- Redis used for caching and rate limiting.
- Celery offloads heavy tasks.
- /chat/history and /memory/export are unpaginated.
- Conversation list does N+1 counts in Supabase path.
- Memory summarization scans per user per day without batching or pagination.

Memory architecture maturity: 6/10
- Multi-tier memory (transient/episodic/core), vector search, retention, and Redis cache are implemented.
- Missing pagination and cache coherence across multi-step writes limits maturity at 10k users with long histories.

Security clarity: 5/10
- Password hashing and JWT issuance exist.
- Optional encryption at rest is supported.
- Rate limiting is present but Redis guard fails open.
- No idempotency keys on writes.
- Migration sets diverge for audit and evolution logging.
