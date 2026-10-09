import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
import redis.asyncio as aioredis

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import text

from app.core.cache import publish_event
from app.core.database import get_db, get_sql_session, has_sql
from app.core.cache import redis_client
from app.core.encryption import decrypt_text
from app.core.security import get_current_user_id
from app.config import settings
from app.schemas.chat import ChatRequest, ChatResponse, PinUpdate, TitleUpdate
from app.services.importance import make_conversation_title, score_message_heuristic
from app.services.fact_store import FactStore
from app.services.memory_layer import chat_tier_for
from app.services.llm_service import QuotaExhausted
from app.services.orchestrator import ConversationOrchestrator
from app.workers.reflection_worker import analyze_reflection

router = APIRouter(prefix="/chat", tags=["chat"])

orchestrator = ConversationOrchestrator()
logger = logging.getLogger(__name__)
BUSY_REPLY = "I'm a bit busy right now - give me a minute and try again."


async def _enforce_message_rate_limit(user_id: str) -> None:
    from app.config import settings
    from datetime import datetime

    day_key = f'msg_day:{user_id}:{datetime.utcnow().strftime("%Y%m%d")}'
    hour_key = f'msg_hour:{user_id}:{datetime.utcnow().strftime("%Y%m%d%H")}'

    try:
        def _check():
            day_count = int(redis_client.incr(day_key))
            if day_count == 1: redis_client.expire(day_key, 86400)
            hour_count = int(redis_client.incr(hour_key))
            if hour_count == 1: redis_client.expire(hour_key, 3600)
            return day_count, hour_count

        day_count, hour_count = await asyncio.to_thread(_check)

        if day_count > settings.MAX_MESSAGES_PER_DAY:
            raise HTTPException(429, 'Daily message limit reached. Resets at midnight.')
        if hour_count > settings.MAX_MESSAGES_PER_HOUR:
            raise HTTPException(429, 'Hourly message limit reached. Try again soon.')
    except HTTPException:
        raise
    except Exception as e:
        # Fail open if Redis is down
        logger.warning(f"Rate limit check failed: {e}")


def _sanitize_error(exc: Exception) -> str:
    """Return a clean user-facing error — never expose raw API responses."""
    err = str(exc).lower()
    if "429" in err or "quota" in err or "resource_exhausted" in err or "rate" in err:
        return "The AI service is at capacity right now. Please try again in a minute."
    if "timeout" in err or "timed out" in err:
        return "The request timed out. Please try again."
    if "connection" in err or "network" in err:
        return "Connection issue. Please check your network and try again."
    return "Something went wrong. Please try again."


def _validate_conversation_owner(conversation_id: str, user_id: str) -> None:
    if not conversation_id:
        return

    if has_sql():
        with get_sql_session() as session:
            owner = session.execute(
                text("SELECT user_id FROM conversations WHERE id = :conversation_id LIMIT 1"),
                {"conversation_id": conversation_id},
            ).scalar()
        if not owner:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if str(owner) != str(user_id):
            raise HTTPException(status_code=403, detail="Conversation does not belong to this user")
        return

    db = get_db()
    response = (
        db.table("conversations")
        .select("user_id")
        .eq("id", conversation_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if str(response.data[0].get("user_id")) != str(user_id):
        raise HTTPException(status_code=403, detail="Conversation does not belong to this user")


def _create_conversation_with_fallback(user_id: str, title: str, sql_session=None) -> str:
    conversation_id = str(uuid4())

    if sql_session is not None:
        try:
            sql_session.execute(
                text("INSERT INTO conversations (id, user_id, title) VALUES (:id, :user_id, :title)"),
                {"id": conversation_id, "user_id": user_id, "title": title},
            )
            return conversation_id
        except Exception:
            logger.exception("Failed to create conversation via provided SQL session")

    elif has_sql():
        try:
            with get_sql_session() as session:
                session.execute(
                    text("INSERT INTO conversations (id, user_id, title) VALUES (:id, :user_id, :title)"),
                    {"id": conversation_id, "user_id": user_id, "title": title},
                )
                return conversation_id
        except Exception:
            logger.exception("Failed to create conversation via SQL fallback")

    try:
        db = get_db()
        res = db.table("conversations").insert({"id": conversation_id, "user_id": user_id, "title": title}).execute()
        if res.data and len(res.data) > 0:
            return res.data[0].get("id", conversation_id)
        return conversation_id
    except Exception:
        logger.exception("Failed to create conversation via Supabase fallback")

    raise HTTPException(status_code=500, detail="Failed to create conversation")


def _touch_conversation_updated_at(conversation_id: str, sql_session=None) -> None:
    now = datetime.now(timezone.utc)
    if sql_session is not None:
        try:
            sql_session.execute(
                text("UPDATE conversations SET updated_at = :updated_at WHERE id = :id"),
                {"updated_at": now, "id": conversation_id},
            )
            return
        except Exception:
            logger.warning("Failed to update conversation timestamp using provided SQL session", exc_info=True)

    if has_sql():
        try:
            with get_sql_session() as session:
                session.execute(
                    text("UPDATE conversations SET updated_at = :updated_at WHERE id = :id"),
                    {"updated_at": now, "id": conversation_id},
                )
            return
        except Exception:
            logger.warning("Failed to update conversation timestamp via SQL", exc_info=True)

    try:
        db = get_db()
        db.table("conversations").update({"updated_at": now.isoformat()}).eq("id", conversation_id).execute()
    except Exception:
        logger.warning("Failed to update conversation timestamp via Supabase", exc_info=True)


def _hydrate_history_row(row: dict) -> dict:
    content = row.get("content")
    if not content and row.get("content_encrypted"):
        try:
            content = decrypt_text(row.get("content_encrypted"))
        except Exception:
            content = ""

    metadata = row.get("metadata")
    if not isinstance(metadata, dict):
        try:
            metadata = json.loads(metadata) if isinstance(metadata, str) else {}
        except json.JSONDecodeError:
            metadata = {}
    if not metadata and row.get("metadata_encrypted"):
        try:
            decrypted = decrypt_text(row.get("metadata_encrypted"))
            metadata = json.loads(decrypted) if decrypted else {}
        except Exception:
            metadata = {}

    timestamp = row.get("created_at") or datetime.now(timezone.utc).isoformat()
    return {
        "id": str(row.get("id")),
        "role": row.get("role") or "assistant",
        "content": content or "",
        "timestamp": str(timestamp),
        "created_at": str(timestamp),
        "metadata": metadata or {},
        "importance_score": float(row.get("importance_score") or 0.0),
    }


def _select_history_page(session, conversation_id: str, limit: int, before: str | None):
    result = session.execute(
        text(
            """
            SELECT * FROM messages
            WHERE conversation_id = :cid
              AND (
                :before IS NULL OR (created_at, CAST(id AS TEXT)) < (
                  SELECT created_at, CAST(id AS TEXT) FROM messages
                  WHERE CAST(id AS TEXT) = :before AND conversation_id = :cid
                )
              )
            ORDER BY created_at DESC, CAST(id AS TEXT) DESC
            LIMIT :fetch_limit
            """
        ),
        {"cid": conversation_id, "before": before, "fetch_limit": limit + 1},
    )
    rows = result.mappings().all()
    has_more = len(rows) > limit
    page = rows[:limit]
    page.reverse()
    return page, has_more


async def _prepare_stream_context(
    user_id: str,
    message: str,
    conversation_id: str,
    sql_session=None,
) -> tuple[dict, list[dict]]:
    identity = orchestrator.identity.get_identity(user_id, sql_session=sql_session) if sql_session is not None else orchestrator.identity.get_identity(user_id)
    memories: list[dict] = []
    try:
        memories = await asyncio.wait_for(
            orchestrator.memory.retrieve_context(
                user_id=user_id,
                query=message,
                limit=5,
                strategy="hybrid",
                conversation_id=conversation_id,
                sql_session=sql_session,
            ),
            timeout=0.9,
        )
    except asyncio.TimeoutError:
        logger.warning("Context retrieval timed out for user %s", user_id)
    except Exception:
        logger.exception("Context retrieval failed during streaming for user %s", user_id)
    return identity, memories


def _fire_and_forget(coro: asyncio.Future, label: str, user_id: str) -> None:
    task = asyncio.create_task(coro)

    def _done_callback(done_task: asyncio.Task) -> None:
        try:
            done_task.result()
        except Exception:
            logger.exception("%s failed for user %s", label, user_id)

    task.add_done_callback(_done_callback)


async def _background_stream_postprocess(
    user_id: str,
    message: str,
    response: str,
    conversation_id: str,
    idempotency_key: str | None = None,
    user_msg_id: str | None = None,
    importance: float | None = None,
) -> None:
    try:
        await orchestrator.memory.store_conversation(
            user_id=user_id,
            role="user",
            content=message,
            conversation_id=conversation_id,
            message_id=user_msg_id,
            metadata={
                "logged_at": datetime.now(timezone.utc).isoformat(),
                "importance": importance if importance is not None else 0.5,
                "memory_tier": chat_tier_for(importance if importance is not None else 0.5),
            },
            idempotency_key=idempotency_key,
        )
        await orchestrator.memory.store_conversation(
            user_id=user_id,
            role="assistant",
            content=response,
            conversation_id=conversation_id,
            metadata={"importance": 0.2, "memory_tier": chat_tier_for(0.2)},
            idempotency_key=f"{idempotency_key}:assistant" if idempotency_key else None,
        )
    except Exception:
        logger.exception("Background memory persistence failed for user %s", user_id)

    try:
        await asyncio.to_thread(
            analyze_reflection.delay,
            user_id,
            {"user": message, "assistant": response},
            user_msg_id,
            message,
        )
        await asyncio.to_thread(publish_event, user_id, {"type": "reflection.queued"})
    except Exception:
        logger.exception("Failed to queue background reflection for user %s", user_id)

    try:
        conflicts = await orchestrator.identity.detect_conflicts(user_id, message)
        if conflicts:
            await asyncio.to_thread(publish_event, user_id, {"type": "identity.conflict", "payload": conflicts})
    except Exception:
        logger.exception("Background conflict detection failed for user %s", user_id)


async def _store_stream_user_message(
    user_id: str,
    message: str,
    conversation_id: str,
    user_msg_id: str,
    idempotency_key: str | None,
    importance: float,
) -> None:
    await orchestrator.memory.store_conversation(
        user_id=user_id,
        role="user",
        content=message,
        conversation_id=conversation_id,
        message_id=user_msg_id,
        metadata={
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "importance": importance,
            "memory_tier": chat_tier_for(importance),
        },
        idempotency_key=idempotency_key,
    )


async def _store_stream_facts(user_id: str, facts, source_message_id: str) -> None:
    if not facts:
        return
    await asyncio.to_thread(FactStore().upsert_facts, user_id, facts, source_message_id)



@router.post("/", response_model=ChatResponse)
async def send_message(request: ChatRequest, user_id: str = Depends(get_current_user_id)):
    conversation_id = request.conversation_id
    idempotency_key = request.idempotency_key

    if conversation_id:
        _validate_conversation_owner(conversation_id, user_id)

    await _enforce_message_rate_limit(user_id)

    if has_sql():
        if not conversation_id:
            conversation_id = _create_conversation_with_fallback(user_id, make_conversation_title(request.message))
        with get_sql_session() as session:
            try:
                result = await orchestrator.handle_message(
                    user_id=user_id,
                    message=request.message,
                    conversation_id=conversation_id,
                    idempotency_key=idempotency_key,
                    sql_session=session,
                )
            except Exception:
                logger.exception("Chat request failed")
                result = {"response": "Fallback response."}

            _touch_conversation_updated_at(conversation_id, sql_session=session)
    else:
        if not conversation_id:
            conversation_id = _create_conversation_with_fallback(user_id, make_conversation_title(request.message))
        try:
            result = await orchestrator.handle_message(
                user_id=user_id,
                message=request.message,
                conversation_id=conversation_id,
                idempotency_key=idempotency_key,
            )
        except Exception:
            logger.exception("Chat request failed on non-SQL path")
            result = {"response": "Fallback response."}
        _touch_conversation_updated_at(conversation_id)

    return ChatResponse(
        response=result.get("response", ""),
        conversation_id=conversation_id,
        insights=result.get("insights"),
        conflicts=result.get("conflicts"),
    )


@router.post("/stream")
async def stream_message(request: ChatRequest, user_id: str = Depends(get_current_user_id)):
    conversation_id = request.conversation_id
    if conversation_id:
        _validate_conversation_owner(conversation_id, user_id)

    await _enforce_message_rate_limit(user_id)

    identity = {}
    memories: list[dict] = []
    prepared_with_sql = False

    if has_sql():
        try:
            with get_sql_session() as session:
                if not conversation_id:
                    conversation_id = _create_conversation_with_fallback(user_id, make_conversation_title(request.message), sql_session=session)
                identity, memories = await _prepare_stream_context(user_id, request.message, conversation_id, sql_session=session)
                prepared_with_sql = True
                _touch_conversation_updated_at(conversation_id, sql_session=session)
        except Exception:
            logger.exception("Streaming prep via SQL failed; falling back")

    if not prepared_with_sql:
        if not conversation_id:
            conversation_id = _create_conversation_with_fallback(user_id, make_conversation_title(request.message))
        identity, memories = await _prepare_stream_context(user_id, request.message, conversation_id)
        _touch_conversation_updated_at(conversation_id)

    user_msg_id = str(uuid4())
    heuristic_facts = []
    try:
        heuristic_facts = score_message_heuristic(request.message)
    except Exception:
        logger.exception("Importance scoring failed for user %s", user_id)
    known_facts = []
    try:
        known_facts = [f["content"] for f in await asyncio.to_thread(FactStore().list_top, user_id, 8)]
    except Exception:
        logger.exception("Known-fact retrieval failed for user %s", user_id)
    _fire_and_forget(_store_stream_facts(user_id, heuristic_facts, user_msg_id), "store_stream_facts", user_id)
    importance = max((fact.importance for fact in heuristic_facts), default=0.1)

    async def event_generator():
        chunks: list[str] = []
        try:
            async for chunk in orchestrator.llm.stream_chat(
                context={"identity": identity, "memories": memories, "patterns": {}, "known_facts": known_facts},
                user_message=request.message,
                identity=identity,
            ):
                if not chunk:
                    continue
                chunks.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except QuotaExhausted:
            logger.info("Gemini quota exhausted for user %s; returning busy reply", user_id)
            _fire_and_forget(
                _store_stream_user_message(
                    user_id=user_id,
                    message=request.message,
                    conversation_id=conversation_id,
                    user_msg_id=user_msg_id,
                    idempotency_key=request.idempotency_key,
                    importance=importance,
                ),
                "store_busy_user_message",
                user_id,
            )
            yield f"data: {json.dumps({'chunk': BUSY_REPLY})}\n\n"
            yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"
            return
        except Exception as exc:
            logger.exception("Streaming response failed for user %s", user_id)
            yield f"data: {json.dumps({'error': _sanitize_error(exc)})}\n\n"
            return

        if not chunks:
            logger.warning("Stream produced no chunks for user %s", user_id)
        response_text = "".join(chunks).strip() or "I'm taking a little longer than usual. Please try again in a moment."
        _fire_and_forget(
            _background_stream_postprocess(
                user_id=user_id,
                message=request.message,
                response=response_text,
                conversation_id=conversation_id,
                idempotency_key=request.idempotency_key,
                user_msg_id=user_msg_id,
                importance=importance,
            ),
            "background_stream_postprocess",
            user_id,
        )
        yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/events/stream")
async def stream_events(
    request: Request,
    since: str | None = Query(None),
    last_event_id: str | None = Header(None),
    user_id: str = Depends(get_current_user_id),
):
    async def event_generator():
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1, socket_timeout=20)
        pubsub = client.pubsub()
        try:
            channel = f"events:{user_id}"
            await pubsub.subscribe(channel)
            if last_event_id or since:
                backlog = await client.lrange(f"events_backlog:{user_id}", -10, -1)
                for event in backlog:
                    yield f"data: {event}\n\n"
            while not await request.is_disconnected():
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=15.0)
                if message and message.get("data"):
                    yield f"data: {message['data']}\n\n"
                else:
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.warning("Chat event subscription failed for user %s", user_id, exc_info=True)
        finally:
            try:
                await pubsub.unsubscribe(f"events:{user_id}")
            except Exception:
                pass
            try:
                await pubsub.close()
            except Exception:
                pass
            await client.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/conversations")
def list_conversations(user_id: str = Depends(get_current_user_id)):
    if has_sql():
        with get_sql_session() as session:
            result = session.execute(
                text(
                    """
                    SELECT c.id, c.title, c.is_pinned, c.created_at, c.updated_at, COUNT(m.id) AS message_count
                    FROM conversations c
                    LEFT JOIN messages m ON m.conversation_id = c.id
                    WHERE c.user_id = :user_id AND (c.is_deleted = false OR c.is_deleted IS NULL)
                    GROUP BY c.id, c.title, c.is_pinned, c.created_at, c.updated_at
                    ORDER BY c.updated_at DESC
                    """
                ),
                {"user_id": user_id},
            )
            return [dict(row) for row in result.mappings().all()]
    db = get_db()
    response = (
        db.table("conversations")
        .select("id, title, is_pinned, created_at, updated_at")
        .eq("user_id", user_id)
        .eq("is_deleted", False)
        .order("updated_at", desc=True)
        .execute()
    )
    return [{**row, "message_count": 0} for row in (response.data or [])]


@router.get("/history")
def get_chat_history(
    conversation_id: str,
    response: Response,
    limit: int = Query(50, ge=1, le=200),
    before: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    if before is not None:
        try:
            UUID(before)
        except (AttributeError, TypeError, ValueError):
            raise HTTPException(status_code=422, detail="before must be a message id")

    _validate_conversation_owner(conversation_id, user_id)

    if has_sql():
        with get_sql_session() as session:
            if before is not None:
                cursor_exists = session.execute(
                    text(
                        """
                        SELECT 1 FROM messages
                        WHERE conversation_id = :conversation_id
                          AND CAST(id AS TEXT) = :before
                        LIMIT 1
                        """
                    ),
                    {"conversation_id": conversation_id, "before": before},
                ).scalar()
                if cursor_exists is None:
                    raise HTTPException(status_code=422, detail="unknown cursor")
            page, has_more = _select_history_page(session, conversation_id, limit, before)
        response.headers["X-Has-More"] = str(has_more).lower()
        return [_hydrate_history_row(dict(row)) for row in page]
    if before is not None:
        db = get_db()
        cursor_exists = (
            db.table("messages")
            .select("id")
            .eq("conversation_id", conversation_id)
            .eq("id", before)
            .limit(1)
            .execute()
        )
        if not cursor_exists.data:
            raise HTTPException(status_code=422, detail="unknown cursor")
    response.headers["X-Has-More"] = "false"
    return []


@router.patch("/conversations/{conversation_id}/title")
def update_title(conversation_id: str, payload: TitleUpdate, user_id: str = Depends(get_current_user_id)):
    _validate_conversation_owner(conversation_id, user_id)
    now = datetime.now(timezone.utc).isoformat()
    if has_sql():
        with get_sql_session() as session:
            session.execute(
                text("UPDATE conversations SET title = :title, updated_at = :now WHERE id = :cid"),
                {"title": payload.title, "cid": conversation_id, "now": now}
            )
            return {"status": "success", "title": payload.title}
    db = get_db()
    db.table("conversations").update({"title": payload.title, "updated_at": now}).eq("id", conversation_id).execute()
    return {"status": "success", "title": payload.title}


@router.patch("/conversations/{conversation_id}/pin")
def update_pin(conversation_id: str, payload: PinUpdate, user_id: str = Depends(get_current_user_id)):
    _validate_conversation_owner(conversation_id, user_id)
    now = datetime.now(timezone.utc).isoformat()
    if has_sql():
        with get_sql_session() as session:
            session.execute(
                text("UPDATE conversations SET is_pinned = :pinned, updated_at = :now WHERE id = :cid"),
                {"pinned": bool(payload.pinned), "cid": conversation_id, "now": now},
            )
    else:
        get_db().table("conversations").update({"is_pinned": payload.pinned, "updated_at": now}).eq("id", conversation_id).execute()
    return {"status": "success", "pinned": payload.pinned}


@router.delete("/conversations")
def clear_all_conversations(user_id: str = Depends(get_current_user_id)):
    """Clear out all past conversations for the user."""
    now = datetime.now(timezone.utc).isoformat()
    if has_sql():
        with get_sql_session() as session:
            session.execute(
                text("UPDATE conversations SET is_deleted = :deleted, updated_at = :now WHERE user_id = :user_id"),
                {"user_id": user_id, "now": now, "deleted": True},
            )
            return {"status": "success", "cleared": True}
    db = get_db()
    db.table("conversations").update({"is_deleted": True, "updated_at": now}).eq("user_id", user_id).execute()
    return {"status": "success", "cleared": True}


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, user_id: str = Depends(get_current_user_id)):
    _validate_conversation_owner(conversation_id, user_id)
    now = datetime.now(timezone.utc).isoformat()
    if has_sql():
        with get_sql_session() as session:
            session.execute(
                text("UPDATE conversations SET is_deleted = :deleted, updated_at = :now WHERE id = :cid"),
                {"cid": conversation_id, "now": now, "deleted": True},
            )
    else:
        get_db().table("conversations").update({"is_deleted": True, "updated_at": now}).eq("id", conversation_id).execute()
    return {"status": "success"}


# ---------------------------------------------------------------------------
# Mind Sanctuary: Grounding, Mental Health & Evolving Persona API
# ---------------------------------------------------------------------------

@router.get("/sanctuary/persona")
def get_sanctuary_persona(user_id: str = Depends(get_current_user_id)):
    """
    Synthesizes a holistic 'Who You Are' living mirror, tracking core anchors,
    current life season, active open loops, and cognitive clarity barometer.
    """
    from app.services.identity_engine import IdentityEngine
    engine = IdentityEngine()
    identity = engine.get_identity(user_id)

    def _get_val(field, default=None):
        if isinstance(identity, dict):
            return identity.get(field, default)
        return getattr(identity, field, default)

    open_loops = _get_val("open_loops", []) or []
    unresolved_loops = [l for l in open_loops if isinstance(l, dict) and l.get("status") != "resolved"]
    unresolved_count = len(unresolved_loops)

    emotions = _get_val("emotions", []) or []
    latest_emotion = emotions[-1] if emotions else None
    primary_emotion = latest_emotion.get("primary_emotion") if isinstance(latest_emotion, dict) else None
    intensity = latest_emotion.get("intensity") if isinstance(latest_emotion, dict) else None

    user_msg_count = 0
    messages_last_7d = 0
    average_emotion_intensity = 0.0
    if has_sql():
        now = datetime.now(timezone.utc)
        cutoff_14d = now - timedelta(days=14)
        cutoff_7d = now - timedelta(days=7)
        with get_sql_session() as session:
            user_msg_count = session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM messages
                    WHERE user_id = :user_id AND role = 'user'
                      AND (delete_at IS NULL OR delete_at > :now)
                      AND created_at >= :cutoff
                    """
                ),
                {"user_id": user_id, "now": now, "cutoff": cutoff_14d},
            ).scalar_one()
            messages_last_7d = session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM messages
                    WHERE user_id = :user_id AND role = 'user'
                      AND (delete_at IS NULL OR delete_at > :now)
                      AND created_at >= :cutoff
                    """
                ),
                {"user_id": user_id, "now": now, "cutoff": cutoff_7d},
            ).scalar_one()
            average_emotion_intensity = session.execute(
                text(
                    """
                    SELECT COALESCE(AVG(intensity), 0)
                    FROM identity_emotions
                    WHERE user_id = :user_id AND created_at >= :cutoff
                    """
                ),
                {"user_id": user_id, "cutoff": cutoff_14d},
            ).scalar_one() or 0.0
    else:
        logger.warning("sanctuary clarity: supabase backend not supported")

    has_enough = user_msg_count >= settings.SANCTUARY_MIN_USER_MESSAGES
    clarity_score = None
    cognitive_load = None
    if has_enough:
        from app.services.clarity import compute_clarity

        clarity_score, cognitive_load = compute_clarity(
            unresolved_count,
            average_emotion_intensity,
            messages_last_7d,
        )

    values = _get_val("values", {}) or {}
    core_anchors = [
        {"label": key, "description": value}
        for key, value in values.items()
        if isinstance(key, str) and isinstance(value, str) and value.strip()
    ] if isinstance(values, dict) else []

    return {
        "status": "success",
        "user_id": user_id,
        "clarity_score": clarity_score,
        "cognitive_load": cognitive_load,
        "primary_emotion": primary_emotion,
        "emotional_intensity": intensity,
        "life_season": None,
        "core_anchors": core_anchors,
        "active_open_loops": unresolved_loops[:8],
        "beliefs": (_get_val("beliefs", []) or [])[:6],
        "patterns": (_get_val("patterns", []) or [])[:5],
        "conflicts": (_get_val("conflicts", []) or [])[:4],
        "grounding_recommendation": (
            "You have multiple unclosed cognitive loops demanding working memory. "
            "A 2-minute mind dump or parking unessential tasks until next week will immediately free up mental bandwidth."
            if unresolved_count > 2 else None
        ),
        "data_sufficiency": None if has_enough else {
            "user_messages": user_msg_count,
            "needed": settings.SANCTUARY_MIN_USER_MESSAGES,
        },
    }


@router.post("/sanctuary/checkin")
def post_sanctuary_checkin(payload: dict, user_id: str = Depends(get_current_user_id)):
    """
    Record an interactive mental health checkin with somatic grounding
    and open-loop cognitive decompression.
    """
    emotion = payload.get("emotion", "Grounded")
    notes = payload.get("notes", "")
    energy = payload.get("energy", "Balanced")

    now = datetime.now(timezone.utc)
    checkin_text = f"[Mental Health Check-in] Feeling {emotion} with {energy} energy. Note: {notes}" if notes else f"[Mental Health Check-in] Feeling {emotion} with {energy} energy."

    checkin_id = str(uuid4())
    from app.core.encryption import encrypt_text
    content_encrypted = encrypt_text(checkin_text)

    if has_sql():
        with get_sql_session() as session:
            session.execute(
                text(
                    """
                    INSERT INTO messages (id, user_id, role, content, content_encrypted, memory_tier, importance_score, created_at)
                    VALUES (:id, :user_id, 'user', :content, :content_encrypted, 'episodic', 0.9, :now)
                    """
                ),
                {
                    "id": checkin_id,
                    "user_id": user_id,
                    "content": checkin_text,
                    "content_encrypted": content_encrypted,
                    "now": now
                }
            )

    return {
        "status": "success",
        "message": "Grounding check-in preserved. Your nervous system anchor is set.",
        "recorded_at": now.isoformat(),
        "companion_reflection": f"I hear you. Acknowledging that you're feeling {emotion.lower()} is the first step toward releasing tension. Your thoughts are safely held in episodic storage."
    }

