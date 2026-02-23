from typing import List, Dict, Any
import math
import json
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session
from app.core.cache import redis_client
from app.core.embeddings import embedding_service
from app.core.encryption import encrypt_text, decrypt_text


class MemoryLayer:
    """
    Multi-tiered memory retrieval system.
    Hybrid: semantic + temporal + importance.
    """

    def __init__(self):
        """
        Initialize MemoryLayer internals and default configuration.
        
        Sets up clients and default parameters used by the memory layer:
        - cache: Redis client for caching and transient storage.
        - embedder: Embedding service used for vectorizing content.
        - supabase: Supabase client when SQL path is unavailable; otherwise None.
        - logger: Module logger.
        - transient_ttl_seconds: Default TTL for transient memories (7200 seconds).
        - episodic_days: Default window (in days) for episodic memory retrieval (7 days).
        - transient_list_max: Maximum number of items kept in the transient list (50).
        """
        self.cache = redis_client
        self.embedder = embedding_service
        self.supabase = get_db() if not has_sql() else None
        self.logger = logging.getLogger(__name__)
        self.transient_ttl_seconds = 2 * 60 * 60
        self.episodic_days = 7
        self.transient_list_max = 50

    async def store_conversation(
        self,
        user_id: str,
        role: str,
        content: str,
        conversation_id: str,
        metadata: Dict[str, Any] | None = None,
    ):
        """
        Store a user's message into the appropriate memory tier and invalidate the user's cache.
        
        Determines storage tier from metadata and content, computes an embedding, then either
        adds the message to the transient in-memory store or persists it to durable storage.
        If persistence fails the error is logged and re-raised; on success the per-user cache index
        is invalidated.
        
        Parameters:
            user_id (str): Identifier of the user owning the message.
            role (str): Message role (e.g., "user", "assistant", "system").
            content (str): Message text to store.
            conversation_id (str): Conversation scope for the message (may affect transient scoping).
            metadata (Dict[str, Any] | None): Optional metadata that may influence tiering and importance.
        
        Raises:
            Exception: Re-raises any exception encountered while persisting the message after logging it.
        """
        embedding = self.embedder.embed(content)
        meta = metadata or {}
        tier = self._decide_tier(meta, content)
        try:
            if tier == "transient":
                self._store_transient(user_id, conversation_id, role, content, meta)
            else:
                await asyncio.to_thread(
                    self._persist_message,
                    user_id,
                    conversation_id,
                    role,
                    content,
                    embedding,
                    meta,
                    tier,
                )
        except Exception:
            self.logger.exception("Failed to persist message for user %s", user_id)
            raise

        self._invalidate_cache(user_id)

    async def retrieve_context(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        strategy: str = "hybrid",
        conversation_id: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memory items for a user based on a query and combine transient and persisted results according to the selected strategy.
        
        Parameters:
            user_id (str): The user identifier whose memories to search.
            query (str): The natural-language query used to find relevant memories.
            limit (int): Maximum number of results to return.
            strategy (str): Scoring strategy to use; one of "hybrid", "semantic", "temporal", or "importance".
            conversation_id (str | None): Optional conversation scope to restrict transient results and cache key; use None for global context.
        
        Returns:
            List[Dict[str, Any]]: A list of memory entries (dictionaries) relevant to the query, truncated to `limit`.
        """
        cache_key = self._build_cache_key(user_id, query, conversation_id)
        cached = self.cache.get(cache_key)
        if cached:
            try:
                return json.loads(cached)[:limit]
            except Exception:
                pass

        query_embedding = self.embedder.embed(query)

        transient_results = self._transient_search(user_id, conversation_id, limit=10)
        semantic_results = self._semantic_search(user_id, query_embedding, limit=15)
        temporal_results = self._temporal_search(user_id, days=self.episodic_days, limit=15)
        important_results = self._importance_search(user_id, threshold=0.7, limit=15)

        if strategy == "hybrid":
            scored = self._hybrid_score(semantic_results, temporal_results, important_results)
        elif strategy == "semantic":
            scored = semantic_results
        elif strategy == "temporal":
            scored = temporal_results
        else:
            scored = important_results

        def _json_safe(obj):
            """
            Produce a JSON-safe string representation of an object.
            
            Parameters:
                obj: The value to convert to a JSON-safe string.
            
            Returns:
                A string representation of `obj` suitable for including in JSON.
            """
            return str(obj)

        combined = self._prepend_transient(transient_results, scored)

        try:
            self.cache.setex(cache_key, 3600, json.dumps(combined[:limit], default=_json_safe))
            index_key = self._cache_index_key(user_id)
            self.cache.sadd(index_key, cache_key)
            self.cache.expire(index_key, 3600)
        except Exception:
            self.logger.debug("Failed to cache context for user %s", user_id)
        return combined[:limit]

    def _semantic_search(self, user_id: str, embedding: List[float], limit: int):
        """
        Retrieve semantically similar, decrypted messages from the user's core memory tier.
        
        Searches for messages for the given user whose semantic similarity to the provided query embedding exceeds 0.7, excludes deleted items, and returns up to `limit` results ordered by similarity.
        
        Parameters:
            user_id (str): ID of the user whose memories are searched.
            embedding (List[float]): Query embedding vector used for semantic matching.
            limit (int): Maximum number of results to return.
        
        Returns:
            List[dict]: Decrypted message records (each containing fields such as `id`, `content`, `metadata`, `importance_score`, `created_at`, and `similarity`) ordered by descending semantic relevance.
        """
        if has_sql():
            vector_literal = self._vector_literal(embedding)
            with get_sql_session() as session:
                result = session.execute(
                    text(
                        """
                        SELECT id, content, metadata, importance_score, created_at,
                               content_encrypted, metadata_encrypted,
                               1 - (embedding <=> CAST(:query_embedding AS vector)) as similarity
                        FROM messages
                        WHERE user_id = :user_id
                          AND memory_tier = 'core'
                          AND (delete_at IS NULL OR delete_at > NOW())
                          AND 1 - (embedding <=> CAST(:query_embedding AS vector)) > :match_threshold
                        ORDER BY embedding <=> CAST(:query_embedding AS vector)
                        LIMIT :match_count
                        """
                    ),
                    {
                        "query_embedding": vector_literal,
                        "match_threshold": 0.7,
                        "match_count": limit,
                        "user_id": user_id,
                    },
                )
                return [self._decrypt_message(dict(row)) for row in result.mappings().all()]

        response = self.supabase.rpc(
            "match_messages",
            {
                "query_embedding": embedding,
                "match_threshold": 0.7,
                "match_count": limit,
                "user_id_filter": user_id,
            },
        ).execute()
        data = response.data or []
        return [self._decrypt_message(dict(row)) for row in data]

    def _temporal_search(self, user_id: str, days: int, limit: int):
        """
        Retrieve episodic messages for a user created within the past `days`, ordered by recency.
        
        Filters out messages that have a `delete_at` timestamp in the past and returns up to `limit` results sorted by `created_at` descending. Returned messages have content and metadata decrypted when applicable.
        
        Parameters:
            user_id (str): ID of the user whose messages to retrieve.
            days (int): Number of past days to include (messages created_at >= now - days).
            limit (int): Maximum number of messages to return.
        
        Returns:
            List[dict]: A list of message dictionaries (with decrypted `content` and `metadata`) ordered newest first, up to `limit`.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        now = datetime.utcnow()

        if has_sql():
            with get_sql_session() as session:
                result = session.execute(
                    text(
                        """
                        SELECT * FROM messages
                        WHERE user_id = :user_id
                          AND memory_tier = 'episodic'
                          AND (delete_at IS NULL OR delete_at > :now)
                          AND created_at >= :cutoff
                        ORDER BY created_at DESC
                        LIMIT :limit
                        """
                    ),
                    {
                        "user_id": user_id,
                        "cutoff": cutoff,
                        "now": now,
                        "limit": limit,
                    },
                )
                return [self._decrypt_message(dict(row)) for row in result.mappings().all()]

        response = (
            self.supabase.table("messages")
            .select("*")
            .eq("user_id", user_id)
            .eq("memory_tier", "episodic")
            .gte("created_at", cutoff.isoformat())
            .or_(f"delete_at.is.null,delete_at.gt.{now.isoformat()}")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        data = response.data or []
        return [self._decrypt_message(dict(row)) for row in data]

    def _importance_search(self, user_id: str, threshold: float, limit: int):
        """
        Retrieve messages for a user with importance at or above a given threshold, ordered by importance.
        
        Parameters:
            user_id (str): ID of the user whose messages to search.
            threshold (float): Minimum importance score to include.
            limit (int): Maximum number of messages to return.
        
        Returns:
            List[dict]: Decrypted message dictionaries matching the criteria, ordered by descending importance and limited to `limit`.
        """
        now = datetime.utcnow()
        if has_sql():
            with get_sql_session() as session:
                result = session.execute(
                    text(
                        """
                        SELECT * FROM messages
                        WHERE user_id = :user_id
                          AND memory_tier IN ('episodic', 'core')
                          AND (delete_at IS NULL OR delete_at > :now)
                          AND importance_score >= :threshold
                        ORDER BY importance_score DESC
                        LIMIT :limit
                        """
                    ),
                    {
                        "user_id": user_id,
                        "threshold": threshold,
                        "now": now,
                        "limit": limit,
                    },
                )
                return [self._decrypt_message(dict(row)) for row in result.mappings().all()]

        response = (
            self.supabase.table("messages")
            .select("*")
            .eq("user_id", user_id)
            .in_("memory_tier", ["episodic", "core"])
            .gte("importance_score", threshold)
            .or_(f"delete_at.is.null,delete_at.gt.{now.isoformat()}")
            .order("importance_score", desc=True)
            .limit(limit)
            .execute()
        )
        data = response.data or []
        return [self._decrypt_message(dict(row)) for row in data]

    def _hybrid_score(self, semantic, temporal, important):
        """
        Compute a combined hybrid score for messages using semantic similarity, recency, and importance.
        
        Parameters:
            semantic (List[Dict[str, Any]]): Messages ranked by semantic similarity; each item must include an "id" and may include "similarity" and "importance_score".
            temporal (List[Dict[str, Any]]): Recent/episodic messages; each item must include an "id" and "created_at" (ISO timestamp) and may include "importance_score".
            important (List[Dict[str, Any]]): Messages selected by importance; each item must include an "id" and may include "importance_score".
        
        Returns:
            List[Dict[str, Any]]: List of message dicts merged from the inputs with an added "hybrid_score" field (weighted combination of semantic, recency, and importance), sorted in descending order by "hybrid_score".
        """
        alpha = 0.5
        beta = 0.3
        gamma = 0.2

        all_messages: Dict[str, Dict[str, Any]] = {}

        for msg in semantic:
            msg_id = msg["id"]
            all_messages[msg_id] = {
                **msg,
                "semantic_score": msg.get("similarity", 0),
                "recency_score": 0,
                "importance_score": msg.get("importance_score", 0.5),
            }

        for msg in temporal:
            msg_id = msg["id"]
            recency = self._compute_recency(msg.get("created_at"))
            if msg_id in all_messages:
                all_messages[msg_id]["recency_score"] = recency
            else:
                all_messages[msg_id] = {
                    **msg,
                    "semantic_score": 0,
                    "recency_score": recency,
                    "importance_score": msg.get("importance_score", 0.5),
                }

        for msg in important:
            msg_id = msg["id"]
            if msg_id not in all_messages:
                all_messages[msg_id] = {
                    **msg,
                    "semantic_score": 0,
                    "recency_score": 0,
                    "importance_score": msg.get("importance_score", 0.5),
                }

        scored = []
        for msg_id, msg in all_messages.items():
            hybrid_score = (
                alpha * msg["semantic_score"] +
                beta * msg["recency_score"] +
                gamma * msg["importance_score"]
            )
            scored.append({**msg, "hybrid_score": hybrid_score})

        scored.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return scored

    def _compute_recency(self, created_at: str | None) -> float:
        if not created_at:
            return 0.0
        lam = 0.1
        created = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        days_ago = (datetime.now(created.tzinfo) - created).days
        return math.exp(-lam * days_ago)

    def _vector_literal(self, embedding: List[float]) -> str:
        return "[" + ",".join(f"{x:.6f}" for x in embedding) + "]"

    def _persist_message(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        tier: str,
    ) -> None:
        """
        Persist a user's message into storage, applying tier-aware encryption and retention.
        
        Parameters:
            user_id (str): ID of the user owning the message.
            conversation_id (str): Conversation scope for the message.
            role (str): Sender role (e.g., "user", "assistant").
            content (str): Plaintext message content to persist.
            embedding (List[float]): Vector embedding for semantic indexing.
            metadata (Dict[str, Any]): Message metadata; may contain an "importance" score.
            tier (str): Memory tier for storage; one of "transient", "episodic", or "core". Episodic and core tiers store encrypted payloads and episodic messages receive a delete_at retention timestamp.
        
        Raises:
            RuntimeError: If no SQL path is available and the Supabase client is not configured.
        """
        importance = metadata.get("importance", 0.5)
        delete_at = None
        if tier == "episodic":
            delete_at = datetime.utcnow() + timedelta(days=self.episodic_days)
        payload = {
            "content": content,
            "metadata": metadata,
            "content_encrypted": None,
            "metadata_encrypted": None,
        }
        if tier in ("episodic", "core"):
            payload = self._encrypt_payload(content, metadata)
        if has_sql():
            vector_literal = self._vector_literal(embedding)
            with get_sql_session() as session:
                session.execute(
                    text(
                        """
                        INSERT INTO messages (
                            user_id, conversation_id, role, content, embedding, metadata,
                            content_encrypted, metadata_encrypted, encryption_version,
                            importance_score, memory_tier, delete_at
                        ) VALUES (
                            :user_id, :conversation_id, :role, :content, :embedding, :metadata,
                            :content_encrypted, :metadata_encrypted, :encryption_version,
                            :importance_score, :memory_tier, :delete_at
                        )
                        """
                    ),
                    {
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "role": role,
                        "content": payload["content"],
                        "embedding": vector_literal,
                        "metadata": json.dumps(payload["metadata"]),
                        "content_encrypted": payload["content_encrypted"],
                        "metadata_encrypted": payload["metadata_encrypted"],
                        "encryption_version": 1,
                        "importance_score": importance,
                        "memory_tier": tier,
                        "delete_at": delete_at,
                    },
                )
                session.commit()
            return

        if not self.supabase:
            raise RuntimeError("Supabase client is not configured")

        self.supabase.table("messages").insert({
            "user_id": user_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": payload["content"],
            "embedding": embedding,
            "metadata": payload["metadata"],
            "importance_score": importance,
            "memory_tier": tier,
            "delete_at": delete_at.isoformat() if delete_at else None,
            "content_encrypted": payload["content_encrypted"],
            "metadata_encrypted": payload["metadata_encrypted"],
            "encryption_version": 1,
        }).execute()

    def _build_cache_key(self, user_id: str, query: str, conversation_id: str | None) -> str:
        """
        Build a deterministic cache key for a user's query scoped to an optional conversation.
        
        Parameters:
            user_id (str): Identifier of the user.
            query (str): The query string to be hashed into the key.
            conversation_id (str | None): Optional conversation scope; uses "global" when None.
        
        Returns:
            cache_key (str): A string key in the form "session:{user_id}:{conversation}:{sha256_digest}" where the digest is a SHA-256 hex of the trimmed query.
        """
        digest = hashlib.sha256(query.strip().encode("utf-8")).hexdigest()
        convo = conversation_id or "global"
        return f"session:{user_id}:{convo}:{digest}"

    def _cache_index_key(self, user_id: str) -> str:
        """
        Build the Redis key used to store the per-user cache index.
        
        Parameters:
            user_id (str): The user's unique identifier.
        
        Returns:
            str: Redis key in the form "session:index:{user_id}".
        """
        return f"session:index:{user_id}"

    def _invalidate_cache(self, user_id: str) -> None:
        """
        Invalidate and remove all cached entries tracked for a user.
        
        This removes every cache key listed in the user's cache index and then deletes the index itself. Byte keys are decoded to UTF-8 before deletion. Errors during cache operations are caught and logged; failures do not raise.
         
        Parameters:
            user_id (str): Identifier of the user whose cache entries should be invalidated.
        """
        index_key = self._cache_index_key(user_id)
        try:
            cached_keys = self.cache.smembers(index_key) or []
            if cached_keys:
                keys = [k.decode("utf-8") if isinstance(k, bytes) else k for k in cached_keys]
                self.cache.delete(*keys)
            self.cache.delete(index_key)
        except Exception:
            self.logger.debug("Failed to invalidate cache for user %s", user_id)

    def _decide_tier(self, metadata: Dict[str, Any], content: str) -> str:
        """
        Determine which memory tier a message should be stored in.
        
        Chooses one of "transient", "episodic", or "core" based on explicit metadata if present, otherwise using importance, an ephemeral flag, and content length/importance heuristics.
        
        Parameters:
        	metadata (Dict[str, Any]): Message metadata; may include "memory_tier" or "tier" (preferred), "importance" (numeric), and "ephemeral" (bool).
        	content (str): The message text used for length-based heuristics.
        
        Returns:
        	tier (str): One of "transient", "episodic", or "core" indicating the storage tier for the message.
        """
        tier = metadata.get("memory_tier") or metadata.get("tier")
        if isinstance(tier, str):
            normalized = tier.strip().lower()
            if normalized in ("transient", "episodic", "core"):
                return normalized
        importance = metadata.get("importance", 0.5)
        if isinstance(importance, (int, float)) and importance >= 0.8:
            return "core"
        if metadata.get("ephemeral") is True:
            return "transient"
        if content and len(content.strip()) <= 80 and importance <= 0.3:
            return "transient"
        return "episodic"

    def _encrypt_payload(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypts message content and metadata for secure storage.
        
        Parameters:
            content (str): Plaintext message content to encrypt.
            metadata (Dict[str, Any]): Message metadata; this will be JSON-serialized before encryption.
        
        Returns:
            Dict[str, Any]: A payload containing either encrypted fields or plaintext fallbacks:
                - If encryption succeeds:
                    - "content": None
                    - "metadata": {}
                    - "content_encrypted": encrypted string of the content
                    - "metadata_encrypted": encrypted string of the JSON-serialized metadata
                - If encryption fails:
                    - "content": original plaintext content
                    - "metadata": original metadata dict
                    - "content_encrypted": None
                    - "metadata_encrypted": None
        """
        encrypted_content = encrypt_text(content)
        encrypted_metadata = encrypt_text(json.dumps(metadata))
        if not encrypted_content or not encrypted_metadata:
            return {
                "content": content,
                "metadata": metadata,
                "content_encrypted": None,
                "metadata_encrypted": None,
            }
        return {
            "content": None,
            "metadata": {},
            "content_encrypted": encrypted_content,
            "metadata_encrypted": encrypted_metadata,
        }

    def _decrypt_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure a message record has plaintext `content` and `metadata` by decrypting encrypted fields when needed.
        
        Parameters:
            msg (Dict[str, Any]): Message dictionary which may contain `content`, `metadata`,
                or encrypted fields `content_encrypted` and `metadata_encrypted`.
        
        Returns:
            Dict[str, Any]: The same message dictionary with `content` set to decrypted text if available,
            and `metadata` set to the decrypted and JSON-parsed object if available (or `{}` if parsing fails).
        """
        content = msg.get("content")
        metadata = msg.get("metadata")
        if content or metadata:
            return msg
        decrypted_content = decrypt_text(msg.get("content_encrypted"))
        decrypted_metadata = decrypt_text(msg.get("metadata_encrypted"))
        if decrypted_content:
            msg["content"] = decrypted_content
        if decrypted_metadata:
            try:
                msg["metadata"] = json.loads(decrypted_metadata)
            except Exception:
                msg["metadata"] = {}
        return msg

    def _transient_key(self, user_id: str, conversation_id: str | None) -> str:
        """
        Build a Redis key for a user's transient memory scoped by conversation.
        
        Parameters:
        	conversation_id (str | None): Conversation identifier; uses "global" when None.
        
        Returns:
        	key (str): Key in the format "transient:{user_id}:{conversation_id_or_global}"
        """
        convo = conversation_id or "global"
        return f"transient:{user_id}:{convo}"

    def _store_transient(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> None:
        """
        Store a message temporarily in the transient Redis list for a user/conversation.
        
        Adds a JSON payload containing an id, content, metadata, importance_score, created_at, role, and memory_tier to the Redis list keyed by the user's transient store, trims the list to the configured max length, and sets the transient TTL.
        
        Parameters:
            user_id (str): ID of the user owning the transient message.
            conversation_id (str): Conversation scope for the transient store (used in the Redis key).
            role (str): Role of the message author (e.g., "user", "assistant").
            content (str): Message text to store.
            metadata (Dict[str, Any]): Additional message metadata; `importance` may be used to set importance_score.
        """
        key = self._transient_key(user_id, conversation_id)
        payload = {
            "id": hashlib.sha256(f"{user_id}:{conversation_id}:{content}".encode("utf-8")).hexdigest(),
            "content": content,
            "metadata": metadata,
            "importance_score": metadata.get("importance", 0.5),
            "created_at": datetime.utcnow().isoformat(),
            "role": role,
            "memory_tier": "transient",
        }
        self.cache.rpush(key, json.dumps(payload))
        self.cache.ltrim(key, -self.transient_list_max, -1)
        self.cache.expire(key, self.transient_ttl_seconds)

    def _transient_search(
        self,
        user_id: str,
        conversation_id: str | None,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve up to `limit` most recent transient messages for a user, optionally scoped to a conversation.
        
        The function reads a Redis list keyed by the user (and conversation if provided), parses stored JSON entries into dictionaries, and ignores any malformed entries. If an error occurs while accessing the cache or parsing items, an empty list is returned.
        
        Parameters:
            user_id (str): The user identifier whose transient messages to fetch.
            conversation_id (str | None): Optional conversation identifier to scope transient messages; pass None for a global per-user transient list.
            limit (int): Maximum number of transient messages to return.
        
        Returns:
            List[Dict[str, Any]]: A list of parsed transient message dictionaries (possibly empty).
        """
        key = self._transient_key(user_id, conversation_id)
        try:
            raw = self.cache.lrange(key, -limit, -1) or []
            items = []
            for item in raw:
                try:
                    items.append(json.loads(item))
                except Exception:
                    continue
            return items
        except Exception:
            return []

    def _prepend_transient(
        self,
        transient: List[Dict[str, Any]],
        scored: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Prepend transient messages to a scored results list, preserving order and deduplicating by message `id`.
        
        Parameters:
            transient (List[Dict[str, Any]]): Ordered list of transient message objects to place at the front.
            scored (List[Dict[str, Any]]): Ordered list of scored/persisted message objects to follow.
        
        Returns:
            List[Dict[str, Any]]: Combined list where transient messages appear first (in their original order) followed by scored messages that do not share an `id` with any transient message. If `transient` is empty, returns `scored` unchanged.
        """
        if not transient:
            return scored
        seen = {msg.get("id") for msg in scored if msg.get("id")}
        combined = list(transient)
        for msg in scored:
            msg_id = msg.get("id")
            if msg_id and msg_id in seen:
                continue
            combined.append(msg)
        return combined
