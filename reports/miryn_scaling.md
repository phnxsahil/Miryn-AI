Database bottleneck
- Write amplification on message inserts; identity/reflection writes and cache invalidation add contention on messages and identities.
- Unpaginated reads in /chat/history and /memory/export scale linearly with memory size.
- N+1 message counts in conversation list (Supabase path).

Vector search bottleneck
- ivfflat recall/latency tradeoff at 2M+ embeddings; lists=100 can degrade recall or latency under load.
- Semantic retrieval runs per request alongside temporal and importance queries.

Token cost bottleneck
- LLM call per message plus reflection LLM calls; 200k+ LLM calls/day at 2k active users.
- Streaming does not reduce token count.

Network bottleneck
- SSE streams keep long-lived connections; 300 concurrent ties up workers.
- Large payloads from export/history endpoints.

Latency bottleneck
- LLM response time dominates request latency.
- Context retrieval fan-out plus embedding generation adds CPU and DB latency.

Top 3 upgrades by ROI per line of code (ordered)
1) Add pagination and hard limits to /chat/history and /memory/export.
2) Rate-limit or sample reflection generation (e.g., every N messages or time window).
3) Replace per-conversation count queries with a single aggregate query or cached counts.
