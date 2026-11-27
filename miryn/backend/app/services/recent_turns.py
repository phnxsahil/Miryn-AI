"""Fetch the most recent turns of the current conversation for prompt context.

Miryn's core promise is conversational continuity, but until now the reply
prompt only contained retrieved memories and stable facts: the model could
not see what was said two messages ago unless semantic retrieval surfaced it.
This helper loads the last N messages of the active conversation so the model
can resolve pronouns, avoid re-asking, and carry the thread naturally.
"""

import logging

from sqlalchemy import text

from app.core.database import get_db, has_sql
from app.core.encryption import decrypt_text

logger = logging.getLogger(__name__)

RECENT_TURNS_LIMIT = 10
RECENT_TURN_MAX_CHARS = 600


def _trim(text_value: str) -> str:
    text_value = (text_value or "").strip()
    if len(text_value) > RECENT_TURN_MAX_CHARS:
        return text_value[: RECENT_TURN_MAX_CHARS - 1].rstrip() + "…"
    return text_value


async def fetch_recent_turns(
    conversation_id: str | None,
    sql_session=None,
    limit: int = RECENT_TURNS_LIMIT,
) -> list[dict]:
    """Return the last `limit` messages of the conversation, oldest first.

    Each item: {"role": "user"|"assistant", "content": str}. Failures are
    non-fatal: continuity is an enhancement, never a reason to fail a reply.
    """
    if not conversation_id:
        return []
    try:
        if has_sql() and sql_session is not None:
            result = sql_session.execute(
                text(
                    """
                    SELECT role, content, content_encrypted
                    FROM messages
                    WHERE conversation_id = :cid
                    ORDER BY created_at DESC, CAST(id AS TEXT) DESC
                    LIMIT :limit
                    """
                ),
                {"cid": conversation_id, "limit": limit},
            )
            rows = [dict(row) for row in result.mappings().all()]
            rows.reverse()
            turns = []
            for row in rows:
                content = row.get("content")
                if not content and row.get("content_encrypted"):
                    try:
                        content = decrypt_text(row.get("content_encrypted"))
                    except Exception:
                        content = ""
                if content:
                    turns.append({"role": row.get("role") or "user", "content": _trim(content)})
            return turns

        db = get_db()
        response = (
            db.table("messages")
            .select("role, content")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = list(response.data or [])
        rows.reverse()
        return [
            {"role": row.get("role") or "user", "content": _trim(row.get("content", ""))}
            for row in rows
            if row.get("content")
        ]
    except Exception:
        logger.exception("Recent-turn fetch failed for conversation %s", conversation_id)
        return []
