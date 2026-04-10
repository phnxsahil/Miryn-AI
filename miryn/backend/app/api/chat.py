from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import text
from app.config import settings
from app.core.database import get_db, has_sql, get_sql_session
from app.core.security import get_current_user_id, get_user_id_from_token
from app.core.cache import drain_events, redis_client
from app.core.encryption import decrypt_text
from app.services.orchestrator import ConversationOrchestrator
from app.workers.reflection_worker import analyze_reflection
from app.schemas.chat import ChatRequest, ChatResponse, TitleUpdate

router = APIRouter(prefix="/chat", tags=["chat"])

orchestrator = ConversationOrchestrator()
logger = logging.getLogger(__name__)


def _validate_conversation_owner(conversation_id: str, user_id: str):
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


@router.post("/", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Handle an incoming chat message, creating a new conversation when no conversation_id is provided, and return the resulting chat response.

    Parameters:
        request: ChatRequest containing the message text and an optional conversation_id.

    Returns:
        ChatResponse: Contains the assistant response text, the conversation_id used or created, optional insights, optional conflicts, detected entities, and detected emotions.

    Raises:
        HTTPException: 404 if a referenced conversation does not exist.
        HTTPException: 403 if a referenced conversation does not belong to the authenticated user.
        HTTPException: 500 if creating a new conversation fails.
    """
    conversation_id = request.conversation_id

    if conversation_id:
        _validate_conversation_owner(conversation_id, user_id)

    # Rate limiting
    day_key = f"msg_day:{user_id}:{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    hour_key = f"msg_hour:{user_id}:{datetime.now(timezone.utc).strftime('%Y%m%d%H')}"
    day_count = int(redis_client.incr(day_key))
    if day_count == 1:
        redis_client.expire(day_key, 86400)
    hour_count = int(redis_client.incr(hour_key))
    if hour_count == 1:
        redis_client.expire(hour_key, 3600)

    if day_count > settings.MAX_MESSAGES_PER_DAY:
        raise HTTPException(status_code=429, detail="Daily message limit reached. Resets at midnight.")
    if hour_count > settings.MAX_MESSAGES_PER_HOUR:
        raise HTTPException(status_code=429, detail="Hourly message limit reached. Try again soon.")

    if has_sql():
        if not conversation_id:
            with get_sql_session() as session:
                result = session.execute(
                    text(
                        """
                        INSERT INTO conversations (user_id, title)
                        VALUES (:user_id, :title)
                        RETURNING id
                        """
                    ),
                    {"user_id": user_id, "title": request.message[:50]},
                ).mappings().first()
                if not result:
                    raise HTTPException(status_code=500, detail="Failed to create conversation")
                conversation_id = str(result["id"])
                session.commit()
    else:
        db = get_db()
        if not conversation_id:
            conv_response = (
                db.table("conversations")
                .insert({
                    "user_id": user_id,
                    "title": request.message[:50],
                })
                .execute()
            )
            if not conv_response or not conv_response.data:
                raise HTTPException(status_code=500, detail="Failed to create conversation")
            conversation_id = conv_response.data[0].get("id")
            if not conversation_id:
                raise HTTPException(status_code=500, detail="Invalid conversation response")

    result = await orchestrator.handle_message(
        user_id=user_id,
        message=request.message,
        conversation_id=conversation_id,
    )

    # Update updated_at
    if has_sql():
        with get_sql_session() as session:
            session.execute(
                text("UPDATE conversations SET updated_at = NOW() WHERE id = :id"),
                {"id": conversation_id}
            )
            session.commit()
    else:
        db = get_db()
        db.table("conversations").update({"updated_at": "now()"}).eq("id", conversation_id).execute()

    return ChatResponse(
        response=result["response"],
        conversation_id=conversation_id,
        insights=result.get("insights"),
        conflicts=result.get("conflicts"),
        entities=result.get("entities"),
        emotions=result.get("emotions"),
    )


@router.post("/stream")
async def stream_message(
    http_request: Request,
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id),
):
    conversation_id = request.conversation_id

    if conversation_id:
        _validate_conversation_owner(conversation_id, user_id)

    # Rate limiting
    day_key = f"msg_day:{user_id}:{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    hour_key = f"msg_hour:{user_id}:{datetime.now(timezone.utc).strftime('%Y%m%d%H')}"
    day_count = int(redis_client.incr(day_key))
    if day_count == 1:
        redis_client.expire(day_key, 86400)
    hour_count = int(redis_client.incr(hour_key))
    if hour_count == 1:
        redis_client.expire(hour_key, 3600)

    if day_count > settings.MAX_MESSAGES_PER_DAY:
        raise HTTPException(status_code=429, detail="Daily message limit reached. Resets at midnight.")
    if hour_count > settings.MAX_MESSAGES_PER_HOUR:
        raise HTTPException(status_code=429, detail="Hourly message limit reached. Try again soon.")

    if has_sql():
        if not conversation_id:
            with get_sql_session() as session:
                result = session.execute(
                    text(
                        """
                        INSERT INTO conversations (user_id, title)
                        VALUES (:user_id, :title)
                        RETURNING id
                        """
                    ),
                    {"user_id": user_id, "title": request.message[:50]},
                ).mappings().first()
                if not result:
                    raise HTTPException(status_code=500, detail="Failed to create conversation")
                conversation_id = str(result["id"])
                session.commit()
    else:
        db = get_db()
        if not conversation_id:
            conv_response = (
                db.table("conversations")
                .insert({
                    "user_id": user_id,
                    "title": request.message[:50],
                })
                .execute()
            )
            if not conv_response or not conv_response.data:
                raise HTTPException(status_code=500, detail="Failed to create conversation")
            conversation_id = conv_response.data[0].get("id")
            if not conversation_id:
                raise HTTPException(status_code=500, detail="Invalid conversation response")

    identity = orchestrator.identity.get_identity(user_id)
    memories = []
    try:
        memories = await orchestrator.memory.retrieve_context(
            user_id=user_id,
            query=request.message,
            limit=5,
            strategy="hybrid",
            conversation_id=conversation_id,
        )
    except Exception:
        memories = []

    context = {
        "identity": identity,
        "memories": memories,
        "patterns": {},
    }

    try:
        await orchestrator.memory.store_conversation(
            user_id=user_id,
            role="user",
            content=request.message,
            conversation_id=conversation_id,
        )
    except Exception as exc:
        logger.warning(
            "Failed to store user message before streaming (user_id=%s, conversation_id=%s): %s",
            user_id, conversation_id, exc, exc_info=True,
        )

    async def event_stream():
        response_parts: list[str] = []
        try:
            async for chunk in orchestrator.llm.stream_chat(
                context=context,
                user_message=request.message,
                identity=identity,
            ):
                if await http_request.is_disconnected():
                    logger.info("Client disconnected from chat stream")
                    return
                response_parts.append(chunk)
                payload = json.dumps({"chunk": chunk})
                yield f"data: {payload}\n\n"
        except Exception as exc:
            logger.exception("Chat stream failed during generation")
            error_msg = str(exc)
            if "timeout" in error_msg.lower():
                error_msg = "Miryn took too long to respond. Please try again."
            else:
                error_msg = "An internal error occurred. Please try again later."
            payload = json.dumps({"error": error_msg})
            yield f"data: {payload}\n\n"
            return

        full_response = "".join(response_parts).strip()
        if full_response:
            try:
                await orchestrator.memory.store_conversation(
                    user_id=user_id,
                    role="assistant",
                    content=full_response,
                    conversation_id=conversation_id,
                )
            except Exception:
                logger.exception("Failed to store assistant response in stream")

            conversation_data = {"user": request.message, "assistant": full_response}
            try:
                analyze_reflection.delay(user_id, conversation_data)
            except Exception:
                logger.warning("Failed to queue reflection from stream")

        done_payload = json.dumps({"done": True, "conversation_id": conversation_id})
        yield f"data: {done_payload}\n\n"

    # Update updated_at
    if has_sql():
        with get_sql_session() as session:
            session.execute(
                text("UPDATE conversations SET updated_at = NOW() WHERE id = :id"),
                {"id": conversation_id}
            )
            session.commit()
    else:
        db = get_db()
        db.table("conversations").update({"updated_at": "now()"}).eq("id", conversation_id).execute()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/conversations")
def list_conversations(user_id: str = Depends(get_current_user_id)):
    if has_sql():
        with get_sql_session() as session:
            result = session.execute(
                text(
                    """
                    SELECT c.id, c.title, c.created_at, c.updated_at,
                           (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as message_count
                    FROM conversations c
                    WHERE c.user_id = :user_id
                    ORDER BY c.updated_at DESC
                    """
                ),
                {"user_id": user_id},
            )
            return [dict(row) for row in result.mappings().all()]

    db = get_db()
    response = (
        db.table("conversations")
        .select("id, title, created_at, updated_at")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    conversations = response.data or []
    for conv in conversations:
        msg_count = db.table("messages").select("id", count="exact").eq("conversation_id", conv["id"]).execute()
        conv["message_count"] = msg_count.count if msg_count else 0
    return conversations


@router.patch("/conversations/{conversation_id}/title")
async def update_title(
    conversation_id: str,
    payload: TitleUpdate,
    user_id: str = Depends(get_current_user_id),
):
    _validate_conversation_owner(conversation_id, user_id)

    new_title = payload.title

    if not new_title:
        if has_sql():
            with get_sql_session() as session:
                first_msg = session.execute(
                    text("SELECT content FROM messages WHERE conversation_id = :cid ORDER BY created_at LIMIT 1"),
                    {"cid": conversation_id}
                ).scalar()
        else:
            db = get_db()
            res = db.table("messages").select("content").eq("conversation_id", conversation_id).order("created_at").limit(1).execute()
            first_msg = res.data[0]["content"] if res.data else None

        if first_msg:
            prompt = f"Generate a very short, 3-5 word title for a conversation that starts with: \"{first_msg[:200]}\". Return only the title text."
            new_title = await orchestrator.llm.generate(prompt)
            new_title = new_title.strip().strip('"')
        else:
            new_title = "New Conversation"

    if has_sql():
        with get_sql_session() as session:
            session.execute(
                text("UPDATE conversations SET title = :title, updated_at = NOW() WHERE id = :id"),
                {"title": new_title, "id": conversation_id}
            )
            session.commit()
    else:
        db = get_db()
        db.table("conversations").update({"title": new_title, "updated_at": "now()"}).eq("id", conversation_id).execute()

    return {"status": "success", "title": new_title}


@router.get("/history")
def get_chat_history(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    Retrieve the ordered message history for a conversation, with encrypted content decrypted when necessary.

    Parameters:
        conversation_id (str): ID of the conversation whose messages to fetch.
        user_id (str): Authenticated user ID (injected dependency); only messages belonging to this user are returned.

    Returns:
        list[dict]: A list of message objects ordered by created_at. Each message will include a content field; if content is missing, it is populated by decrypting content_encrypted.
    """
    if has_sql():
        with get_sql_session() as session:
            result = session.execute(
                text(
                    """
                    SELECT * FROM messages
                    WHERE conversation_id = :conversation_id
                      AND user_id = :user_id
                    ORDER BY created_at
                    """
                ),
                {"conversation_id": conversation_id, "user_id": user_id},
            )
            rows = [dict(row) for row in result.mappings().all()]
            for row in rows:
                if not row.get("content"):
                    row["content"] = decrypt_text(row.get("content_encrypted"))
            return rows

    db = get_db()
    response = (
        db.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )

    data = response.data or []
    for row in data:
        if not row.get("content"):
            row["content"] = decrypt_text(row.get("content_encrypted"))
    return data


@router.get("/events/stream")
async def stream_events(request: Request, authorization: str | None = Header(default=None)):
    """
    Stream server-sent events for the authenticated user.

    Parameters:
        request (Request): FastAPI request object used to detect client disconnection.
        authorization (str | None): Optional Authorization header as Bearer token.

    Returns:
        StreamingResponse: An SSE stream yielding JSON-encoded event objects.

    Raises:
        HTTPException: 401 if no authentication token is provided or token is invalid.
    """
    token: str | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "", 1).strip()
    else:
        token = request.query_params.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    try:
        user_id = get_user_id_from_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    async def event_stream():
        try:
            while True:
                if await request.is_disconnected():
                    break
                events = await asyncio.to_thread(drain_events, user_id, 50)
                for event in events:
                    payload = json.dumps(event)
                    yield f"data: {payload}\n\n"
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            return

    return StreamingResponse(event_stream(), media_type="text/event-stream")