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
        digest = hashlib.sha256(query.strip().encode("utf-8")).hexdigest()
        convo = conversation_id or "global"
        return f"session:{user_id}:{convo}:{digest}"

    def _cache_index_key(self, user_id: str) -> str:
        return f"session:index:{user_id}"

    def _invalidate_cache(self, user_id: str) -> None:
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
