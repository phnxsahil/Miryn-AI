"""Encrypted SQL storage for durable life facts."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from app.config import settings
from app.core.database import get_db, get_sql_session, has_sql
from app.core.encryption import decrypt_text, encrypt_text, encryption_available
from app.services.importance import ScoredFact, clean_fact_text, fact_key

logger = logging.getLogger(__name__)
_missing_encryption_logged = False


_CORRECTION_STOPWORDS = {
    "the", "a", "an", "of", "to", "at", "on", "in", "for", "my", "their",
    "is", "am", "are", "was", "were", "i", "im",
}


def _correction_tokens(value: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9']+", value.lower())
        if token not in _CORRECTION_STOPWORDS and len(token) >= 2
    ]


def _tokens_match(needles: list[str], haystack: list[str]) -> bool:
    def _one(needle: str, hay: str) -> bool:
        if hay == needle:
            return True
        # Morphological tolerance only (hate/hates, coriander/coriander's):
        # prefix match where the shared stem is at least 4 characters, so
        # short words cannot collide (entity "Goa" must not match "goal").
        shorter, longer = (needle, hay) if len(needle) <= len(hay) else (hay, needle)
        return len(shorter) >= 4 and longer.startswith(shorter)

    return all(any(_one(needle, hay) for hay in haystack) for needle in needles)


def select_supersede_candidate(
    candidates: list[dict[str, Any]],
    new_fact: dict[str, Any],
    corrects: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Pick the single fact an explicit correction supersedes, or None.

    Fail-closed: any missing field, identical old/new value, missing polarity
    flip on a preference correction, zero or multiple eligible candidates all
    return None, leaving every existing fact active and visible. Manual
    memories are never eligible targets.
    """
    if not isinstance(corrects, dict):
        return None
    entity = str(corrects.get("entity") or "").strip()
    attribute = str(corrects.get("attribute") or "").strip()
    old_value = str(corrects.get("old_value") or "").strip()
    new_value = str(corrects.get("new_value") or "").strip()
    if not (entity and attribute and old_value and new_value):
        return None
    if old_value.lower() == new_value.lower():
        return None
    category = new_fact.get("category")
    if category == "preference":
        # A stance correction is only meaningful with a polarity flip; without
        # both polarities there is no evidence the stance actually changed.
        polarity_old = str(corrects.get("polarity_old") or "").strip().lower()
        polarity_new = str(corrects.get("polarity_new") or "").strip().lower()
        if not (polarity_old and polarity_new) or polarity_old == polarity_new:
            return None
    entity_tokens = _correction_tokens(entity)
    value_tokens = _correction_tokens(old_value)
    if not entity_tokens or not value_tokens:
        return None
    new_created = new_fact.get("created_at")
    eligible: list[dict[str, Any]] = []
    for row in candidates:
        if row.get("extractor") == "manual":
            continue
        if row.get("category") != category:
            continue
        created = row.get("created_at")
        if new_created is not None and created is not None and not (created < new_created):
            continue
        text_tokens = _correction_tokens(str(row.get("text") or ""))
        if not text_tokens:
            continue
        if not _tokens_match(entity_tokens, text_tokens):
            continue
        if not _tokens_match(value_tokens, text_tokens):
            continue
        eligible.append(row)
    if len(eligible) != 1:
        return None
    return eligible[0]


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
        global _missing_encryption_logged
        if not encryption_available():
            if not _missing_encryption_logged:
                logger.warning("memory facts unavailable: encryption key missing")
                _missing_encryption_logged = True
            return []
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
            if content is None:
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
            deleted = bool(result.rowcount)
        if deleted:
            # Do not silently retain correction payloads about a deleted fact:
            # audit rows referencing it are derived data and go with it.
            # Best effort and separate, so a pre-migration database (no audit
            # table) still deletes the fact itself.
            try:
                with get_sql_session() as session:
                    session.execute(
                        text(
                            """
                            DELETE FROM memory_fact_supersessions
                            WHERE user_id = :user_id
                              AND (old_fact_id = :fact_id OR new_fact_id = :fact_id)
                            """
                        ),
                        {"user_id": user_id, "fact_id": fact_id},
                    )
            except Exception:
                logger.warning("supersession audit cleanup failed for fact %s", fact_id)
        return deleted

    def link_explicit_corrections(
        self,
        user_id: str,
        facts: list[ScoredFact],
        source_message_id: str | None = None,
    ) -> list[dict[str, str]]:
        """Supersede facts that a new explicit correction provably replaces.

        Only links made through select_supersede_candidate are applied, inside
        one transaction per message, and each link is recorded in
        memory_fact_supersessions for audit/rollback. Ambiguity (zero or
        multiple candidates) leaves every fact active.
        """
        if not settings.MEMORY_SUPERSESSION_ENABLED:
            return []
        correcting = [fact for fact in facts if getattr(fact, "corrects", None)]
        if not correcting:
            return []
        if not has_sql():
            self._unsupported()
            return []
        if not encryption_available():
            # No link without its audit row: the audit payload must be
            # Fernet-encrypted like memory_facts.fact, so a missing key
            # disables linking entirely instead of hiding a fact silently.
            logger.error("supersession linking skipped: encryption unavailable")
            return []
        links: list[dict[str, str]] = []
        with get_sql_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT id, fact, category, extractor, created_at
                    FROM memory_facts
                    WHERE user_id = :user_id AND status = 'active'
                    """
                ),
                {"user_id": user_id},
            ).mappings().all()
            candidates: list[dict[str, Any]] = []
            for row in rows:
                try:
                    content = decrypt_text(row["fact"])
                except Exception:
                    continue
                if content is None:
                    continue
                candidates.append(
                    {
                        "id": str(row["id"]),
                        "text": content,
                        "category": row["category"],
                        "extractor": row["extractor"],
                        "created_at": row["created_at"],
                    }
                )
            for fact in correcting:
                new_row = next(
                    (c for c in candidates if fact_key(c["text"]) == fact_key(fact.text)),
                    None,
                )
                if new_row is None:
                    continue
                pool = [c for c in candidates if c["id"] != new_row["id"]]
                chosen = select_supersede_candidate(pool, new_row, fact.corrects)
                if chosen is None:
                    continue
                updated = session.execute(
                    text(
                        """
                        UPDATE memory_facts
                        SET status = 'superseded', superseded_by = :new_id, updated_at = NOW()
                        WHERE id = :old_id AND user_id = :user_id AND status = 'active'
                        """
                    ),
                    {"new_id": new_row["id"], "old_id": chosen["id"], "user_id": user_id},
                )
                if not updated.rowcount:
                    continue
                # Encryption parity with memory_facts.fact: the audit payload
                # carries the user's own values, so it is encrypted at rest
                # rather than stored as plaintext JSONB.
                encrypted_corrects = encrypt_text(json.dumps(fact.corrects))
                if not encrypted_corrects:
                    # Fail the whole transaction rather than commit a status
                    # flip without its audit row.
                    raise RuntimeError("supersession audit encryption failed")
                session.execute(
                    text(
                        """
                        INSERT INTO memory_fact_supersessions (
                            user_id, old_fact_id, new_fact_id, source_message_id, corrects
                        ) VALUES (
                            :user_id, :old_id, :new_id, :source_message_id, :corrects
                        )
                        """
                    ),
                    {
                        "user_id": user_id,
                        "old_id": chosen["id"],
                        "new_id": new_row["id"],
                        "source_message_id": source_message_id,
                        "corrects": encrypted_corrects,
                    },
                )
                links.append({"old_fact_id": chosen["id"], "new_fact_id": new_row["id"]})
        return links

    def restore_superseded(self, user_id: str, fact_id: str) -> str:
        """Restore a superseded fact to active when that is safe.

        Returns "restored", "conflict" (an active row with the same fact_key
        already exists, so restoring would violate the partial unique index or
        silently recreate a contradiction), or "not_found". On conflict the
        row stays superseded and nothing changes.
        """
        if not has_sql():
            self._unsupported()
            return "not_found"
        with get_sql_session() as session:
            row = session.execute(
                text(
                    """
                    SELECT id, fact_key, status FROM memory_facts
                    WHERE id = :fact_id AND user_id = :user_id
                    """
                ),
                {"fact_id": fact_id, "user_id": user_id},
            ).mappings().first()
            if not row or row["status"] != "superseded":
                return "not_found"
            conflict = session.execute(
                text(
                    """
                    SELECT 1 FROM memory_facts
                    WHERE user_id = :user_id AND fact_key = :fact_key
                      AND status = 'active' AND id <> :fact_id
                    LIMIT 1
                    """
                ),
                {"user_id": user_id, "fact_key": row["fact_key"], "fact_id": fact_id},
            ).first()
            if conflict:
                return "conflict"
            session.execute(
                text(
                    """
                    UPDATE memory_facts
                    SET status = 'active', superseded_by = NULL, updated_at = NOW()
                    WHERE id = :fact_id AND user_id = :user_id AND status = 'superseded'
                    """
                ),
                {"fact_id": fact_id, "user_id": user_id},
            )
            session.execute(
                text(
                    """
                    UPDATE memory_fact_supersessions
                    SET restored_at = NOW()
                    WHERE old_fact_id = :fact_id AND user_id = :user_id AND restored_at IS NULL
                    """
                ),
                {"fact_id": fact_id, "user_id": user_id},
            )
            return "restored"

    def list_supersessions(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Decrypted supersession audit history for export/review."""
        if not has_sql():
            self._unsupported()
            return []
        try:
            with get_sql_session() as session:
                rows = session.execute(
                    text(
                        """
                        SELECT id, old_fact_id, new_fact_id, source_message_id,
                               corrects, created_at, restored_at
                        FROM memory_fact_supersessions
                        WHERE user_id = :user_id
                        ORDER BY created_at DESC
                        LIMIT :limit
                        """
                    ),
                    {"user_id": user_id, "limit": limit},
                ).mappings().all()
        except Exception:
            logger.warning("memory_fact_supersessions unavailable for user %s", user_id)
            return []
        history: list[dict[str, Any]] = []
        for row in rows:
            payload = None
            try:
                raw = decrypt_text(row["corrects"])
                payload = json.loads(raw) if raw else None
            except Exception:
                payload = None
            history.append(
                {
                    "id": str(row["id"]),
                    "old_fact_id": str(row["old_fact_id"]),
                    "new_fact_id": str(row["new_fact_id"]),
                    "source_message_id": str(row["source_message_id"]) if row["source_message_id"] else None,
                    "corrects": payload,
                    "created_at": row["created_at"],
                    "restored_at": row["restored_at"],
                }
            )
        return history
