# Miryn Project Summary (Full-Stack)

Miryn is a context-aware AI companion that maintains persistent memory, evolving identity, and reflective insights across conversations. The system is built end-to-end with a FastAPI backend, a Next.js 14 frontend, and a Postgres/pgvector + Redis data layer, all orchestrated via Docker Compose.

Key capabilities:
- Persistent, multi-tier memory retrieval using pgvector for semantic search
- Identity system with versioned traits, values, beliefs, and open loops
- Reflection pipeline that extracts insights and generates concise, empathetic summaries
- Secure auth flows, rate limiting, and audit logging
- Full-stack UX with onboarding, chat, and identity dashboard

Tech stack:
- Backend: FastAPI, Supabase/Postgres, pgvector, Redis
- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Infra: Docker Compose