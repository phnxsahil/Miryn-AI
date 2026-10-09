"""Encrypted SQL storage for durable life facts."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from app.config import settings
from app.core.database import get_db, get_sql_session, has_sql
from app.core.encryption import decrypt_text, encrypt_text
from app.services.importance import ScoredFact, clean_fact_text, fact_key

logger = logging.getLogger(__name__)


def bumped_importance(old: float, new: float) -> float:
    base = max(old, new)
    if base >= 1.0:
        return base
    return min(0.99, base + (1.0 - base) * 0.15)


class FactStore:
    def _unsupported(self) -> None:
        logger.warning("memory_facts: supabase backend not supported")

    def upsert_facts(self, user_id: str, facts: list[ScoredFact], source_message_id: str | None = None) -> None:
        candidates = [
            fact for fact in facts
            if fact.category != "chitchat"
            and fact.importance >= settings.IMPORTANCE_CORE_THRESHOLD * 0.8
        ]
        if not candidates:
            return
        encrypted = [(fact, encrypt_text(fact.text)) for fact in candidates]
        saved = [(fact, cipher) for fact, cipher in encrypted if cipher]
        skipped = len(encrypted) - len(saved)
        if skipped:
            logger.error("skipping %d facts: encryption unavailable", skipped)
        if not saved:
            return
        if not has_sql():
            self._unsupported()
            return
        with get_sql_session() as session:
            for fact, encrypted_fact in saved:
                session.execute(
                    text(
                        """
                        INSERT INTO memory_facts (
                            user_id, fact, fact_key, category, importance, emotional_weight,
                            source_message_id, extractor
                        ) VALUES (
                            :user_id, :fact, :fact_key, :category, :importance, :emotional_weight,
                            :source_message_id, :extractor
                        )
                        ON CONFLICT (user_id, fact_key) WHERE status = 'active'
                        DO UPDATE SET
                            mention_count = memory_facts.mention_count + 1,
                            importance = CASE
                                WHEN memory_facts.extractor = 'manual' OR EXCLUDED.extractor = 'manual'
                                    THEN GREATEST(memory_facts.importance, EXCLUDED.importance)
                                ELSE LEAST(0.99, GREATEST(memory_facts.importance, EXCLUDED.importance)
                                    + (1.0 - GREATEST(memory_facts.importance, EXCLUDED.importance)) * 0.15)
                            END,
                            emotional_weight = GREATEST(memory_facts.emotional_weight, EXCLUDED.emotional_weight),
                            last_seen_at = NOW(),
                            updated_at = NOW()
                        """
                    ),
                    {
                        "user_id": user_id,
                        "fact": encrypted_fact,
                        "fact_key": fact_key(fact.text),
                        "category": fact.category,
                        "importance": fact.importance,
                        "emotional_weight": fact.emotional_weight,
                        "source_message_id": source_message_id,
                        "extractor": fact.extractor,
                    },
                )

    def replace_heuristic_for_message(
        self,
        user_id: str,
        source_message_id: str | None,
        llm_facts: list[ScoredFact],
    ) -> None:
        if not source_message_id:
            return
        if not has_sql():
            self._unsupported()
            return
        with get_sql_session() as session:
            session.execute(
                text(
                    """
                    UPDATE memory_facts
                    SET status = 'deleted', updated_at = NOW()
                    WHERE user_id = :user_id
                      AND source_message_id = :source_message_id
                      AND extractor = 'heuristic'
                      AND mention_count = 1
                    """
                ),
                {"user_id": user_id, "source_message_id": source_message_id},
            )
        if llm_facts:
            self.upsert_facts(user_id, llm_facts, source_message_id)

    def _list(self, user_id: str, limit: int, minimum: float | None = None) -> list[dict[str, Any]]:
        if not has_sql():
            self._unsupported()
            return []
        where_importance = "AND importance >= :minimum" if minimum is not None else ""
        params: dict[str, Any] = {"user_id": user_id, "limit": limit}
        if minimum is not None:
            params["minimum"] = minimum
        with get_sql_session() as session:
            rows = session.execute(
                text(
                    f"""
                    SELECT id, fact, importance, created_at, last_seen_at, extractor
                    FROM memory_facts
                    WHERE user_id = :user_id AND status = 'active' {where_importance}
                    ORDER BY importance DESC, mention_count DESC, last_seen_at DESC
                    LIMIT :limit
                    """
                ),
                params,
            ).mappings().all()
        result = []
        for row in rows:
            try:
                content = decrypt_text(row["fact"])
            except Exception:
                continue
            if row["extractor"] == "heuristic":
                content = clean_fact_text(content)
            result.append(
                {
                    "id": str(row["id"]),
                    "content": content,
                    "memory_tier": "core" if minimum is not None else "episodic",
                    "importance_score": row["importance"],
                    "created_at": row["created_at"],
                }
            )
        return result

    def list_core(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._list(user_id, limit, settings.IMPORTANCE_CORE_THRESHOLD)

    def list_top(self, user_id: str, n: int = 8) -> list[dict[str, Any]]:
        return self._list(user_id, n)

    def create_manual(self, user_id: str, text_value: str) -> dict[str, Any] | None:
        if not has_sql():
            self._unsupported()
            return None
        manual = ScoredFact(text_value.strip(), "manual", 1.0, 0.0, "manual")
        self.upsert_facts(user_id, [manual])
        if not has_sql():
            return None
        with get_sql_session() as session:
            row = session.execute(
                text(
                    """
                    SELECT id, fact, importance, created_at
                    FROM memory_facts
                    WHERE user_id = :user_id AND fact_key = :fact_key AND status = 'active'
                    LIMIT 1
                    """
                ),
                {"user_id": user_id, "fact_key": fact_key(text_value)},
            ).mappings().first()
        if not row:
            return None
        return {
            "id": str(row["id"]),
            "content": text_value.strip(),
            "memory_tier": "core",
            "importance_score": row["importance"],
            "created_at": row["created_at"],
        }

    def soft_delete(self, user_id: str, fact_id: str) -> bool:
        if not has_sql():
            self._unsupported()
            return False
        with get_sql_session() as session:
            result = session.execute(
                text(
                    """
                    UPDATE memory_facts
                    SET status = 'deleted', updated_at = NOW()
                    WHERE id = :fact_id AND user_id = :user_id AND status = 'active'
                    """
                ),
                {"fact_id": fact_id, "user_id": user_id},
            )
            return bool(result.rowcount)
