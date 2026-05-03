import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text

from app.core.cache import drain_events, publish_event
from app.core.database import get_db, get_sql_session, has_sql
from app.core.encryption import decrypt_text
from app.core.security import get_current_user_id, get_user_id_from_token
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.orchestrator import ConversationOrchestrator
from app.workers.reflection_worker import analyze_reflection

router = APIRouter(prefix="/chat", tags=["chat"])

orchestrator = ConversationOrchestrator()
logger = logging.getLogger(__name__)


def _enforce_message_rate_limit(user_id: str) -> None:
    # Demo build: rate limiting intentionally bypassed.
    del user_id
    return


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
        db.table("conversations").insert({"id": conversation_id, "user_id": user_id, "title": title}).execute()
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
) -> None:
    try:
        entities_payload = []
        emotions_payload = {}
        try:
            from app.services.ds_service import ds_service

            entities_payload, emotions_payload = await asyncio.gather(
                asyncio.to_thread(ds_service.extract_entities, message),
                asyncio.to_thread(ds_service.detect_emotions, message),
            )
        except Exception:
            logger.exception("Background DS inference failed for user %s", user_id)
            entities_payload, emotions_payload = [], {}

        await orchestrator.memory.store_conversation(
            user_id=user_id,
            role="user",
            content=message,
            conversation_id=conversation_id,
            metadata={
                "entities": entities_payload if isinstance(entities_payload, list) else [],
                "emotions": emotions_payload if isinstance(emotions_payload, dict) else {},
                "logged_at": datetime.now(timezone.utc).isoformat(),
            },
            idempotency_key=idempotency_key,
        )
        await orchestrator.memory.store_conversation(
            user_id=user_id,
            role="assistant",
            content=response,
            conversation_id=conversation_id,
            idempotency_key=f"{idempotency_key}:assistant" if idempotency_key else None,
        )
    except Exception:
        logger.exception("Background memory persistence failed for user %s", user_id)

    try:
        await asyncio.to_thread(
            analyze_reflection.delay,
            user_id,
            {"user": message, "assistant": response},
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


@router.post("/", response_model=ChatResponse)
async def send_message(request: ChatRequest, user_id: str = Depends(get_current_user_id)):
    conversation_id = request.conversation_id
    idempotency_key = request.idempotency_key

    if conversation_id:
        _validate_conversation_owner(conversation_id, user_id)

    _enforce_message_rate_limit(user_id)

    if has_sql():
        with get_sql_session() as session:
            if not conversation_id:
                conversation_id = _create_conversation_with_fallback(user_id, request.message[:50], sql_session=session)

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
            conversation_id = _create_conversation_with_fallback(user_id, request.message[:50])
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
        entities=result.get("entities"),
        emotions=result.get("emotions"),
    )


@router.post("/stream")
async def stream_message(request: ChatRequest, user_id: str = Depends(get_current_user_id)):
    conversation_id = request.conversation_id
    if conversation_id:
        _validate_conversation_owner(conversation_id, user_id)

    _enforce_message_rate_limit(user_id)

    identity = {}
    memories: list[dict] = []
    prepared_with_sql = False

    if has_sql():
        try:
            with get_sql_session() as session:
                if not conversation_id:
                    conversation_id = _create_conversation_with_fallback(user_id, request.message[:50], sql_session=session)
                identity, memories = await _prepare_stream_context(user_id, request.message, conversation_id, sql_session=session)
                prepared_with_sql = True
                _touch_conversation_updated_at(conversation_id, sql_session=session)
        except Exception:
            logger.exception("Streaming prep via SQL failed; falling back")

    if not prepared_with_sql:
        if not conversation_id:
            conversation_id = _create_conversation_with_fallback(user_id, request.message[:50])
        identity, memories = await _prepare_stream_context(user_id, request.message, conversation_id)
        _touch_conversation_updated_at(conversation_id)

    async def event_generator():
        chunks: list[str] = []
        try:
            async for chunk in orchestrator.llm.stream_chat(
                context={"identity": identity, "memories": memories, "patterns": {}},
                user_message=request.message,
                identity=identity,
            ):
                if not chunk:
                    continue
                chunks.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as exc:
            logger.exception("Streaming response failed for user %s", user_id)
            error_message = str(exc) or "Streaming failed"
            yield f"data: {json.dumps({'error': error_message})}\n\n"
            return

        response_text = "".join(chunks).strip() or "I'm taking a little longer than usual. Please try again in a moment."
        _fire_and_forget(
            _background_stream_postprocess(
                user_id=user_id,
                message=request.message,
                response=response_text,
                conversation_id=conversation_id,
                idempotency_key=request.idempotency_key,
            ),
            "background_stream_postprocess",
            user_id,
        )
        yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/events/stream")
async def stream_events(
    token: str | None = Query(default=None),
    user_id: str = Query(default=""),
):
    resolved_user_id = user_id
    if token:
        resolved_user_id = get_user_id_from_token(token)
    if not resolved_user_id:
        raise HTTPException(status_code=401, detail="Missing chat events token")

    async def event_generator():
        while True:
            events = await asyncio.to_thread(drain_events, resolved_user_id, 50)
            if events:
                for event in events:
                    yield f"data: {json.dumps(event)}\n\n"
            else:
                yield ": keep-alive\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/conversations")
def list_conversations(user_id: str = Depends(get_current_user_id)):
    if has_sql():
        with get_sql_session() as session:
            result = session.execute(
                text(
                    """
                    SELECT c.id, c.title, c.created_at, c.updated_at, COUNT(m.id) AS message_count
                    FROM conversations c
                    LEFT JOIN messages m ON m.conversation_id = c.id
                    WHERE c.user_id = :user_id
                    GROUP BY c.id, c.title, c.created_at, c.updated_at
                    ORDER BY c.updated_at DESC
                    """
                ),
                {"user_id": user_id},
            )
            return [dict(row) for row in result.mappings().all()]
    return []


@router.get("/history")
def get_chat_history(conversation_id: str, user_id: str = Depends(get_current_user_id)):
    _validate_conversation_owner(conversation_id, user_id)

    if has_sql():
        with get_sql_session() as session:
            result = session.execute(
                text("SELECT * FROM messages WHERE conversation_id = :cid ORDER BY created_at ASC"),
                {"cid": conversation_id},
            )
            return [_hydrate_history_row(dict(row)) for row in result.mappings().all()]
    return []
