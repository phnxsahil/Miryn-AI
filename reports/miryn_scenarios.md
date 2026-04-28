Scenario A - 10,000 memory entries
- What breaks? /memory/export and /chat/history pull entire sets without pagination; response size and latency spike. Memory retrieval limits to small N, but export/history endpoints do not.
- Where does data inconsistency occur? memory_summaries and messages are decoupled; summaries can describe deleted content after retention or deletes.
- Where does memory drift happen? Context cache is per-query for 1 hour and only invalidated on store_conversation; deletions via /memory/{id} do not invalidate cached query keys.
- Is there risk of duplicate embeddings? Low per message if unique, but repeated imports or retries can create duplicates with new IDs; no dedupe guard.
- Is there risk of stale memory being retrieved? High if cache returns items past delete_at; cache not invalidated on deletes.
- What is the first architectural bottleneck? Unpaginated reads for export/history and N+1 counts on conversations (Supabase path).

Scenario B - 5 rapid messages concurrently (multi-tab)
- What breaks? Conversation creation and updated_at updates are non-transactional and repeated per request; multiple tabs can create multiple conversations for one intent.
- Where does data inconsistency occur? Fire-and-forget store_conversation tasks can reorder messages; updated_at can be out of sync with message order.
- Where does memory drift happen? Cached context can be reused before async writes complete; transient Redis list may not include latest persisted messages.
- Is there risk of duplicate embeddings? Medium. Same text in multiple tabs yields multiple identical embeddings stored as distinct rows.
- Is there risk of stale memory being retrieved? High during bursts due to cached context and async write latency.
- What is the first architectural bottleneck? Redis rate limit and cache paths per message plus concurrent LLM calls saturating provider limits.

Scenario C - Embedding API fails mid-request
- What breaks? Embed falls back to deterministic hash; request succeeds but semantic quality degrades.
- Where does data inconsistency occur? Mixed embedding sources (real vs hash) in the same table with no provenance; similarity scores become inconsistent.
- Where does memory drift happen? Hash embeddings bias retrieval toward irrelevant matches; hybrid scoring blends those results into context.
- Is there risk of duplicate embeddings? Low; hash is deterministic per text but still inserted as new rows.
- Is there risk of stale memory being retrieved? Unchanged; cache can serve older results despite embedding quality changes.
- What is the first architectural bottleneck? Embedding path is synchronous via asyncio.to_thread; failure increases CPU hashing for each message.

Scenario D - Vector search returns irrelevant memories
- What breaks? No hard failure, but response quality degrades and reflection writes drift identity based on wrong context.
- Where does data inconsistency occur? None at storage level; inconsistency is semantic (wrong memories influence outputs).
- Where does memory drift happen? Reflection writes emotions/patterns/open loops from bad context, persisting errors into identity stores.
- Is there risk of duplicate embeddings? No direct change from normal operation.
- Is there risk of stale memory being retrieved? Elevated if irrelevant results are cached for 1 hour for similar queries.
- What is the first architectural bottleneck? Retrieval quality depends on embedding quality and ivfflat index tuning; low match_threshold or weak index tuning yields noisy neighbors.
