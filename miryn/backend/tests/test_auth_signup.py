import uuid
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.main import app
import app.api.auth as auth
from app.core.security import create_access_token, create_refresh_token


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


class _FakeCursor:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return self

    def first(self):
        return self._row


class _FakeSession:
    def __init__(self, insert_row=None, select_row=None, insert_exc=None):
        self._insert_row = insert_row
        self._select_row = select_row
        self._insert_exc = insert_exc

    def execute(self, stmt, params=None):
        sql = str(stmt)
        if "INSERT INTO users" in sql:
            if self._insert_exc:
                raise self._insert_exc
            return _FakeCursor(self._insert_row)
        if "SELECT id, email FROM users" in sql:
            return _FakeCursor(self._select_row)
        raise AssertionError(f"Unexpected SQL: {sql}")


def test_signup_sql_insert_returns_none_then_selects(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    user_id = uuid.uuid4()
    session = _FakeSession(
        insert_row=None,
        select_row={"id": user_id, "email": "test@example.com"},
    )

    @contextmanager
    def _fake_get_sql_session():
        yield session

    monkeypatch.setattr(auth, "has_sql", lambda: True)
    monkeypatch.setattr(auth, "get_sql_session", _fake_get_sql_session)

    res = client.post("/auth/signup", json={"email": "TEST@EXAMPLE.COM", "password": "password123"})
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == str(user_id)
    assert body["email"] == "test@example.com"


def test_signup_sql_duplicate_email_returns_400(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    session = _FakeSession(
        insert_exc=IntegrityError("stmt", {}, Exception("duplicate")),
    )

    @contextmanager
    def _fake_get_sql_session():
        yield session

    monkeypatch.setattr(auth, "has_sql", lambda: True)
    monkeypatch.setattr(auth, "get_sql_session", _fake_get_sql_session)

    res = client.post("/auth/signup", json={"email": "test@example.com", "password": "password123"})
    assert res.status_code == 400
    assert "already" in res.json().get("detail", "").lower()


def test_signup_supabase_duplicate_email_returns_400(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class DummyPostgrestAPIError(Exception):
        pass

    class _FakeSupabase:
        def table(self, _name):
            return self

        def insert(self, _payload):
            return self

        def execute(self):
            raise DummyPostgrestAPIError({"code": "23505", "message": "duplicate key value violates unique constraint"})

    monkeypatch.setattr(auth, "has_sql", lambda: False)
    monkeypatch.setattr(auth, "get_db", lambda: _FakeSupabase())
    monkeypatch.setattr(auth, "PostgrestAPIError", DummyPostgrestAPIError)

    res = client.post("/auth/signup", json={"email": "test@example.com", "password": "password123"})
    assert res.status_code == 400
    assert "already" in res.json().get("detail", "").lower()


def test_signup_supabase_missing_data_returns_500(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class DummyPostgrestAPIError(Exception):
        pass

    class _Resp:
        data = []

    class _FakeSupabase:
        def table(self, _name):
            return self

        def insert(self, _payload):
            return self

        def execute(self):
            return _Resp()

    monkeypatch.setattr(auth, "has_sql", lambda: False)
    monkeypatch.setattr(auth, "get_db", lambda: _FakeSupabase())
    monkeypatch.setattr(auth, "PostgrestAPIError", DummyPostgrestAPIError)

    res = client.post("/auth/signup", json={"email": "test@example.com", "password": "password123"})
    assert res.status_code == 500


def test_refresh_accepts_refresh_token_body(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(auth, "has_sql", lambda: False)

    class _FakeSupabase:
        def table(self, _name):
            return self

        def select(self, _fields):
            return self

        def eq(self, _field, _value):
            return self

        def limit(self, _value):
            return self

        def execute(self):
            class _Resp:
                data = [{"id": "user-1", "email": "test@example.com", "is_deleted": False}]

            return _Resp()

    monkeypatch.setattr(auth, "get_db", lambda: _FakeSupabase())

    res = client.post("/auth/refresh", json={"refresh_token": create_refresh_token("user-1")})
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["id"] == "user-1"


def test_refresh_rejects_access_token_in_refresh_body(client: TestClient):
    res = client.post("/auth/refresh", json={"refresh_token": create_access_token("user-1")})
    assert res.status_code == 401

