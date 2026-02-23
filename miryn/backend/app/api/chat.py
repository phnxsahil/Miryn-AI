from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import StreamingResponse
import asyncio
import json
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session
from app.core.security import get_current_user_id, get_user_id_from_token
from app.core.cache import drain_events
from app.core.encryption import decrypt_text
from app.services.orchestrator import ConversationOrchestrator
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

orchestrator = ConversationOrchestrator()


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


@router.get("/history")
def get_chat_history(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
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
    token: str | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "", 1).strip()
    else:
        token = request.query_params.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    user_id = get_user_id_from_token(token)
    async def event_stream():
        try:
            while True:
                if await request.is_disconnected():
                    break
                events = drain_events(user_id, limit=50)
                for event in events:
                    payload = json.dumps(event)
                    yield f"data: {payload}\n\n"
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            return

    return StreamingResponse(event_stream(), media_type="text/event-stream")
