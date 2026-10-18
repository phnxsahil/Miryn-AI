import asyncio

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app
from app.api import chat
from app.api.chat import get_current_user_id
from app.schemas.chat import ChatRequest

client = TestClient(app)

# Mock a valid UUID
MOCK_USER_ID = "00000000-0000-0000-0000-000000000000"

@pytest.fixture
def mock_user():
    app.dependency_overrides[get_current_user_id] = lambda: MOCK_USER_ID
    yield
    app.dependency_overrides.clear()

@patch("app.api.chat.redis_client")
@patch("app.api.chat.orchestrator.handle_message")
@patch("app.api.chat.has_sql")
@patch("app.api.chat.get_db")
def test_chat_rate_limit_daily(mock_get_db, mock_has_sql, mock_handle_message, mock_redis, mock_user):
    # Mock redis to return a value over the limit for daily
    mock_redis.incr.side_effect = lambda key: 51 if "msg_day" in key else 1
    mock_redis.expire.return_value = True
    mock_has_sql.return_value = False # Use Supabase path
    
    response = client.post("/chat/", json={"message": "hello"})
    
    assert response.status_code == 429
    assert "Daily message limit reached" in response.json()["detail"]

@patch("app.api.chat.redis_client")
@patch("app.api.chat.orchestrator.handle_message")
@patch("app.api.chat.has_sql")
@patch("app.api.chat.get_db")
def test_chat_rate_limit_hourly(mock_get_db, mock_has_sql, mock_handle_message, mock_redis, mock_user):
    # Mock redis to return a value over the limit for hourly
    mock_redis.incr.side_effect = lambda key: 21 if "msg_hour" in key else 1
    mock_redis.expire.return_value = True
    mock_has_sql.return_value = False
    
    response = client.post("/chat/", json={"message": "hello"})
    
    assert response.status_code == 429
    assert "Hourly message limit reached" in response.json()["detail"]

@patch("app.api.chat.redis_client")
@patch("app.api.chat.orchestrator.handle_message")
@patch("app.api.chat.has_sql")
@patch("app.api.chat.get_db")
def test_chat_rate_limit_ok(mock_get_db, mock_has_sql, mock_handle_message, mock_redis, mock_user):
    # Mock redis to return values within limits
    mock_redis.incr.return_value = 1
    mock_redis.expire.return_value = True
    mock_has_sql.return_value = False
    
    # Mock database
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock conversation creation
    mock_db.table().insert().execute.return_value = MagicMock(data=[{"id": "conv-123"}])
    # Mock updated_at refresh
    mock_db.table().update().eq().execute.return_value = MagicMock()
    
    mock_handle_message.return_value = {"response": "hi", "conversation_id": "conv-123"}
    
    response = client.post("/chat/", json={"message": "hello"})
    
    assert response.status_code == 200
    assert response.json()["response"] == "hi"


@patch("app.api.chat.redis_client")
@patch("app.api.chat.get_db")
@patch("app.api.chat.get_sql_session")
@patch("app.api.chat.has_sql")
def test_chat_stream_falls_back_when_sql_session_unavailable(
    mock_has_sql,
    mock_get_sql_session,
    mock_get_db,
    mock_redis,
    mock_user,
):
    mock_redis.incr.return_value = 1
    mock_redis.expire.return_value = True
    mock_has_sql.side_effect = [True, False, False]
    mock_get_sql_session.side_effect = RuntimeError("sql unavailable")

    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    mock_db.table().insert().execute.return_value = MagicMock(data=[{"id": "conv-stream"}])
    mock_db.table().update().eq().execute.return_value = MagicMock()

    async def fake_stream_chat(*args, **kwargs):
        yield "hello"

    with patch("app.api.chat.orchestrator.identity.get_identity", return_value={}), \
         patch("app.api.chat.orchestrator.memory.retrieve_context", new=AsyncMock(return_value=[])), \
         patch("app.api.chat.orchestrator.memory.store_conversation", new=AsyncMock(return_value=None)), \
         patch("app.api.chat.orchestrator.llm.stream_chat", fake_stream_chat), \
         patch("app.api.chat.analyze_reflection.delay", return_value=None):
        response = client.post("/chat/stream", json={"message": "hello"})

    assert response.status_code == 200
    assert '"chunk": "hello"' in response.text
    assert '"conversation_id": "conv-stream"' in response.text


def test_chat_stream_saves_sentence_complete_reply():
    incomplete = "Instead of bringing relief"
    scheduled = []

    async def fake_stream_chat(*args, **kwargs):
        yield incomplete

    async def drain():
        await asyncio.gather(*(coro for coro, _, _ in scheduled))

    async def exercise():
        response = await chat.stream_message(ChatRequest(message="How am I really doing?"), MOCK_USER_ID)
        events = [event async for event in response.body_iterator]
        await drain()
        return events

    with patch("app.api.chat._enforce_message_rate_limit", new=AsyncMock()), \
         patch("app.api.chat.has_sql", return_value=False), \
         patch("app.api.chat._create_conversation_with_fallback", return_value="conv-complete"), \
         patch("app.api.chat._touch_conversation_updated_at"), \
         patch("app.api.chat._prepare_stream_context", new=AsyncMock(return_value=({}, []))), \
         patch("app.api.chat.score_message_heuristic", return_value=[]), \
         patch("app.api.chat.FactStore") as fact_store, \
         patch("app.api.chat._store_stream_facts", new=AsyncMock()), \
         patch("app.api.chat.orchestrator.llm.stream_chat", fake_stream_chat), \
         patch("app.api.chat.orchestrator.llm.complete_sentence", new=AsyncMock(return_value=", it left you looking for something steadier.")), \
         patch("app.api.chat.analyze_reflection.delay", return_value=None), \
         patch("app.api.chat._fire_and_forget", side_effect=lambda coro, label, user_id: scheduled.append((coro, label, user_id))), \
         patch("app.api.chat._background_stream_postprocess", new=AsyncMock()) as postprocess:
        fact_store.return_value.list_top.return_value = []
        events = asyncio.run(exercise())

    assert any("steadier." in event for event in events)
    saved_reply = postprocess.call_args.kwargs["response"]
    assert saved_reply.endswith((".", "!", "?"))
