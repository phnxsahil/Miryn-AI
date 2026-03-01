from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session
from app.core.security import get_current_user_id, get_user_id_from_token
from app.core.cache import drain_events
from app.core.encryption import decrypt_text
from app.services.orchestrator import ConversationOrchestrator
from app.workers.reflection_worker import analyze_reflection
from app.schemas.chat import ChatRequest, ChatResponse

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
        ChatResponse: Contains the assistant `response` text, the `conversation_id` used or created, optional `insights`, and optional `conflicts`.
    
    Raises:
        HTTPException: 404 if a referenced conversation does not exist.
        HTTPException: 403 if a referenced conversation does not belong to the authenticated user.
        HTTPException: 500 if creating a new conversation fails.
    """
    conversation_id = request.conversation_id

    if conversation_id:
        _validate_conversation_owner(conversation_id, user_id)

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

    return ChatResponse(
        response=result["response"],
        conversation_id=conversation_id,
        insights=result.get("insights"),
        conflicts=result.get("conflicts"),
    )


@router.post("/stream")
async def stream_message(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id),
):
    conversation_id = request.conversation_id

    if conversation_id:
        _validate_conversation_owner(conversation_id, user_id)

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
    except Exception:
        pass

    async def event_stream():
        response_parts: list[str] = []
        try:
            async for chunk in orchestrator.llm.stream_chat(
                context=context,
                user_message=request.message,
                identity=identity,
            ):
                if await request.is_disconnected():
                    return
                response_parts.append(chunk)
                payload = json.dumps({"chunk": chunk})
                yield f"data: {payload}\n\n"
        except Exception as exc:
            logger.exception("Chat stream failed")
            payload = json.dumps({"error": "Something went wrong"})
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
                pass

            conversation_data = {"user": request.message, "assistant": full_response}
            try:
                analyze_reflection.delay(user_id, conversation_data)
            except Exception:
                pass

        done_payload = json.dumps({"done": True, "conversation_id": conversation_id})
        yield f"data: {done_payload}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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
        list[dict]: A list of message objects ordered by `created_at`. Each message will include a `content` field; if `content` is missing, it is populated by decrypting `content_encrypted`.
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
    Stream server-sent events (SSE) of user-specific events authenticated by a token.
    
    Parameters:
        request (Request): FastAPI request object used to detect client disconnection and read query params.
        authorization (str | None): Optional Authorization header expected as "Bearer <token>"; if absent the function will look for a "token" query parameter.
    
    Returns:
        StreamingResponse: An SSE stream (media type "text/event-stream") that yields JSON-encoded event objects for the authenticated user. Each SSE message is prefixed with "data: " and separated by a blank line.
    
    Raises:
        HTTPException: 401 if no authentication token is provided.
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
        """
        Stream server-sent events (SSE) for the authenticated user by yielding JSON-encoded event payloads in SSE format.
        
        The generator continuously polls recent events (up to 50 at a time) and yields each as an SSE data frame (a single string "data: <json>\n\n"). The loop exits when the client disconnects or when the coroutine is cancelled.
        
        Returns:
            str: SSE-formatted data frames containing a JSON-encoded event, e.g. "data: { ... }\n\n".
        """
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
