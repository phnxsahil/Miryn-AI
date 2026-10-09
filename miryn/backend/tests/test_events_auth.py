from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app


client = TestClient(app)


def test_events_stream_requires_authorization_header():
    response = client.get("/chat/events/stream")
    assert response.status_code == 401


def test_events_stream_rejects_query_token_without_header():
    token = create_access_token("events-user")
    response = client.get("/chat/events/stream", params={"token": token})
    assert response.status_code == 401
