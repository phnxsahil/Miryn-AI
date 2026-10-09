from datetime import datetime, timezone
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session
from app.core.security import get_current_user_id
from uuid import uuid4
from app.core.encryption import decrypt_text, encrypt_text
from app.services.identity_engine import IdentityEngine
from app.services.fact_store import FactStore

router = APIRouter(prefix="/memory", tags=["memory"])
identity_engine = IdentityEngine()
logger = logging.getLogger(__name__)


def _hydrate_message(row: dict) -> dict:
    content = row.get("content")
    if not content and row.get("content_encrypted"):
        try:
            content = decrypt_text(row.get("content_encrypted"))
        except Exception:
            content = None

    metadata = row.get("metadata")
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = None
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
    if not isinstance(metadata, dict):
        return False
    if isinstance(metadata.get("primary_emotion"), str):
        return True
    emotions = metadata.get("emotions") if isinstance(metadata.get("emotions"), dict) else None
    return isinstance(emotions.get("primary_emotion"), str) if emotions else False


def _strip_memory_fields(item: dict) -> dict:
    return {k: v for k, v in item.items() if k not in {"metadata", "role"}}


def _clamp_limit(limit: int) -> int:
    return min(max(limit, 1), 200)


def _get_all_memories(user_id: str, limit: int, offset: int) -> list[dict]:
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
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {"user_id": user_id, "now": now, "limit": limit, "offset": offset},
            ).mappings().all()
            return [_hydrate_message(dict(row)) for row in rows]

    db = get_db()
    response = (
        db.table("messages")
        .select("*")
        .eq("user_id", user_id)
        .or_(f"delete_at.is.null,delete_at.gt.{now.isoformat()}")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return [_hydrate_message(row) for row in (response.data or [])]


@router.get("/export")
def export_user_data(
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    limit = _clamp_limit(limit)
    identity = identity_engine.get_identity(user_id)
    memories = _get_all_memories(user_id, limit, offset)
    facts = FactStore().list_top(user_id, limit)
    return JSONResponse(
        content=jsonable_encoder({
            "identity": identity,
            "memories": memories,
            "facts": facts,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }),
        headers={"Content-Disposition": "attachment; filename=miryn_data.json"},
    )


@router.get("/")
def get_memory(
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    limit = _clamp_limit(limit)
    facts = FactStore().list_core(user_id, limit)
    emotions: list[dict] = []
    if has_sql():
        with get_sql_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT id, primary_emotion, intensity, created_at
                    FROM identity_emotions
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """
                ),
                {"user_id": user_id, "limit": min(limit, 10)},
            ).mappings().all()
        emotions = [
            {
                "id": str(row["id"]),
                "content": f"Felt {row['primary_emotion']} ({row['intensity']})",
                "memory_tier": "episodic",
                "importance_score": None,
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    else:
        logger.warning("memory_facts: supabase backend not supported")
    return {"facts": facts, "emotions": emotions, "recent": []}


@router.delete("/purge/episodic")
def purge_episodic_memories(user_id: str = Depends(get_current_user_id)):
    now = datetime.now(timezone.utc)
    if has_sql():
        with get_sql_session() as session:
            result = session.execute(
                text(
                    """
                    UPDATE messages
                    SET delete_at = :now
                    WHERE user_id = :user_id
                      AND memory_tier = 'episodic'
                      AND (delete_at IS NULL OR delete_at > :now)
                    """
                ),
                {"now": now, "user_id": user_id},
            )
            return {"status": "success", "purged_count": result.rowcount}

    db = get_db()
    response = (
        db.table("messages")
        .update({"delete_at": now.isoformat()})
        .eq("user_id", user_id)
        .eq("memory_tier", "episodic")
        .execute()
    )
    return {"status": "success", "purged_count": len(response.data or [])}


@router.delete("/{message_id}")
def delete_memory(message_id: str, user_id: str = Depends(get_current_user_id)):
    now = datetime.now(timezone.utc)

    if FactStore().soft_delete(user_id, message_id):
        return {"message": "Memory removed"}

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

@router.post("/")
def create_memory(payload: dict, user_id: str = Depends(get_current_user_id)):
    content = payload.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Memory content cannot be empty")
    fact = FactStore().create_manual(user_id, content)
    if fact is None:
        return {"status": "unavailable"}
    return {"status": "success", **fact}
