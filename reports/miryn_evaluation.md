Scores
1) Backend engineering interviewer: 6/10
2) Early-stage startup CTO: 5/10
3) YC technical founder review: 4/10

Backend engineering interviewer
- What prevents 9/10? Unpaginated endpoints, inconsistent migration sets (backend vs Supabase), non-atomic write sequences, and weak idempotency on write paths.
- Architectural blind spots: lack of transactional boundaries across multi-step writes, cache invalidation gaps, and mixed embedding provenance without tracking.
- Failure modes not modeled: Redis failure fail-open behavior in rate limiting and login guards, LLM provider throttling, and partial failure of identity sub-store writes.
- Demo-ready or company-ready? Demo-ready. Not company-ready due to concurrency and data integrity risks.

Early-stage startup CTO
- What prevents 9/10? Operational fragility under concurrency, cost exposure from reflection LLM calls, and missing pagination for long-term memory access.
- Architectural blind spots: long-lived SSE connections without backpressure, lack of idempotency keys, and no clear strategy for memory growth and retention at scale.
- Failure modes not modeled: retries leading to duplicate writes, timeouts in background workers, and out-of-order message persistence.
- Demo-ready or company-ready? Demo-ready. Not company-ready until cost and consistency controls are added.

YC technical founder review
- What prevents 9/10? Scalability limits are apparent; LLM cost per message is high; data model divergence between SQL and Supabase migrations creates uncertainty.
- Architectural blind spots: no pagination or cursoring for history/export, no robust queueing for high-concurrency messaging, and poor observability for memory drift.
- Failure modes not modeled: vector search returning irrelevant memories at scale, embedding service fallback leading to semantic degradation, and cache serving stale context.
- Demo-ready or company-ready? Demo-ready. Not company-ready for 10k users without targeted scalability fixes.
