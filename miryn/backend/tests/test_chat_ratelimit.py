import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app
from app.api.chat import get_current_user_id

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
