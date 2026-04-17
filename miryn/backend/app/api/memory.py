from datetime import datetime, timezone
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session
from app.core.security import get_current_user_id
from app.core.encryption import decrypt_text
from app.services.identity_engine import IdentityEngine
from app.services.memory_ranker import rank_memories

router = APIRouter(prefix="/memory", tags=["memory"])
identity_engine = IdentityEngine()


def _hydrate_message(row: dict) -> dict:
    content = row.get("content")
    if not content and row.get("content_encrypted"):
        try:
            content = decrypt_text(row.get("content_encrypted"))
        except Exception:
            content = None

    metadata = row.get("metadata")
    if not metadata and row.get("metadata_encrypted"):
        try:
            metadata = json.loads(decrypt_text(row.get("metadata_encrypted")))
        except Exception:
            metadata = None

    return {
        "id": row.get("id"),
        "content": content,
        "memory_tier": row.get("memory_tier"),
        "importance_score": row.get("importance_score"),
        "created_at": row.get("created_at"),
        "metadata": metadata,
        "role": row.get("role"),
    }


def _has_primary_emotion(metadata: dict | None) -> bool:
    if not metadata:
        return False
    if isinstance(metadata.get("primary_emotion"), str):
        return True
    emotions = metadata.get("emotions") if isinstance(metadata.get("emotions"), dict) else None
    return isinstance(emotions.get("primary_emotion"), str) if emotions else False


def _strip_memory_fields(item: dict) -> dict:
    return {k: v for k, v in item.items() if k not in {"metadata", "role"}}


def _get_all_memories(user_id: str) -> list[dict]:
    now = datetime.now(timezone.utc)
    if has_sql():
        with get_sql_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT * FROM messages
                    WHERE user_id = :user_id
                      AND (delete_at IS NULL OR delete_at > :now)
                    ORDER BY created_at DESC
                    """
                ),
                {"user_id": user_id, "now": now},
            ).mappings().all()
            return [_hydrate_message(dict(row)) for row in rows]

    db = get_db()
    response = (
        db.table("messages")
        .select("*")
        .eq("user_id", user_id)
        .or_(f"delete_at.is.null,delete_at.gt.{now.isoformat()}")
        .order("created_at", desc=True)
        .execute()
    )
    return [_hydrate_message(row) for row in (response.data or [])]


@router.get("/export")
def export_user_data(user_id: str = Depends(get_current_user_id)):
    identity = identity_engine.get_identity(user_id)
    memories = _get_all_memories(user_id)
    return JSONResponse(
        content={
            "identity": identity,
            "memories": memories,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        },
        headers={"Content-Disposition": "attachment; filename=miryn_data.json"},
    )


@router.get("/")
def get_memory(user_id: str = Depends(get_current_user_id)):
    now = datetime.utcnow()

    if has_sql():
        with get_sql_session() as session:
            facts_rows = session.execute(
                text(
                    """
                    SELECT id, content, content_encrypted, metadata, metadata_encrypted, memory_tier, importance_score, created_at
                    FROM messages
                    WHERE user_id = :user_id
                      AND role = 'assistant'
                      AND memory_tier = 'core'
                      AND (delete_at IS NULL OR delete_at > :now)
                    ORDER BY created_at DESC
                    """
                ),
                {"user_id": user_id, "now": now},
            ).mappings().all()

            recent_rows = session.execute(
                text(
                    """
                    SELECT id, content, content_encrypted, metadata, metadata_encrypted, memory_tier, importance_score, created_at
                    FROM messages
                    WHERE user_id = :user_id
                      AND (delete_at IS NULL OR delete_at > :now)
                    ORDER BY created_at DESC
                    LIMIT 10
                    """
                ),
                {"user_id": user_id, "now": now},
            ).mappings().all()

            emotion_rows = session.execute(
                text(
                    """
                    SELECT id, content, content_encrypted, metadata, metadata_encrypted, memory_tier, importance_score, created_at
                    FROM messages
                    WHERE user_id = :user_id
                      AND (delete_at IS NULL OR delete_at > :now)
                      AND (
                        (metadata->'emotions'->>'primary_emotion') IS NOT NULL
                        OR (metadata->>'primary_emotion') IS NOT NULL
                      )
                    ORDER BY created_at DESC
                    LIMIT 50
                    """
                ),
                {"user_id": user_id, "now": now},
            ).mappings().all()

        facts = [_hydrate_message(dict(row)) for row in facts_rows]
        recent = [_hydrate_message(dict(row)) for row in recent_rows]
        emotions = []
        for row in emotion_rows:
            item = _hydrate_message(dict(row))
            if _has_primary_emotion(item.get("metadata")):
                emotions.append(item)

        return {
            "facts": [_strip_memory_fields(item) for item in facts],
            "emotions": [_strip_memory_fields(item) for item in emotions],
            "recent": [_strip_memory_fields(item) for item in recent],
        }

    db = get_db()
    base = (
        db.table("messages")
        .select("id, content, content_encrypted, metadata, metadata_encrypted, memory_tier, importance_score, created_at, role, delete_at")
        .eq("user_id", user_id)
        .or_(f"delete_at.is.null,delete_at.gt.{now.isoformat()}")
        .order("created_at", desc=True)
        .limit(200)
        .execute()
    )
    rows = base.data or []
    hydrated = [_hydrate_message(row) for row in rows]

    facts = [
        item for item in hydrated
        if item.get("memory_tier") == "core" and item.get("role") == "assistant"
    ]
    emotions = [item for item in hydrated if _has_primary_emotion(item.get("metadata"))]
    recent = hydrated[:10]

    return {
        "facts": [_strip_memory_fields(item) for item in facts],
        "emotions": [_strip_memory_fields(item) for item in emotions],
        "recent": [_strip_memory_fields(item) for item in recent],
    }


@router.delete("/{message_id}")
def delete_memory(message_id: str, user_id: str = Depends(get_current_user_id)):
    now = datetime.utcnow()

    if has_sql():
        with get_sql_session() as session:
            result = session.execute(
                text(
                    """
                    UPDATE messages
                    SET delete_at = :now
                    WHERE id = :message_id AND user_id = :user_id
                    """
                ),
                {"now": now, "message_id": message_id, "user_id": user_id},
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Memory not found")
        return {"message": "Memory removed"}

    db = get_db()
    response = (
        db.table("messages")
        .update({"delete_at": now.isoformat()})
        .eq("id", message_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"message": "Memory removed"}

@router.get("/ranked")
def get_ranked_memories(user_id: str = Depends(get_current_user_id)):
    """
    Returns all memories ranked by XGBoost relevance model.
    Adds relevance_score to each memory.
    """
    now = datetime.now(timezone.utc)
    memories = _get_all_memories(user_id)

    # Build feature-ready dicts
    ranked = []
    for item in memories:
        created_at = item.get("created_at")
        if created_at:
            try:
                if isinstance(created_at, str):
                    created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                else:
                    created_dt = created_at
                days_ago = max(0, (now - created_dt).days)
            except Exception:
                days_ago = 30
        else:
            days_ago = 30

        metadata = item.get("metadata") or {}
        emotions = metadata.get("emotions") or {}

        ranked.append({
            "id": item.get("id"),
            "content": item.get("content"),
            "memory_tier": item.get("memory_tier"),
            "importance_score": item.get("importance_score"),
            "created_at": item.get("created_at"),
            "days_ago": days_ago,
            "emotional_intensity": float(emotions.get("intensity", 0.5)) if emotions else 0.5,
            "entity_overlap": int(metadata.get("entity_overlap", 0)),
            "identity_alignment": 1 if item.get("memory_tier") == "core" else 0,
        })

    ranked = rank_memories(ranked)
    return {"ranked_memories": ranked}
