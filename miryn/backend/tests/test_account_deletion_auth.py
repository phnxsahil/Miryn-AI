"""Tokens for deleted or missing accounts must stop authenticating.

Account deletion anonymizes the user row and sets is_deleted, but JWTs are
stateless. The refresh endpoint already refuses deleted accounts; these
tests pin the same guarantee for the access-token path used by every
authenticated endpoint, for both database backends, with no real accounts
or tokens.
"""
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine, text

import app.core.security as security
from app.core.security import create_access_token, create_refresh_token, get_current_user_id


def _creds(token):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _sql_backend(monkeypatch, rows):
    from sqlalchemy.pool import StaticPool
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    with engine.begin() as setup:
        setup.execute(text("CREATE TABLE users (id TEXT PRIMARY KEY, is_deleted INTEGER)"))
        for uid, deleted in rows:
            setup.execute(text("INSERT INTO users (id, is_deleted) VALUES (:id, :d)"), {"id": uid, "d": deleted})
    @contextmanager
    def _session():
        connection = engine.connect()
        try:
            yield connection
        finally:
            connection.close()
    monkeypatch.setattr(security, "has_sql", lambda: True)
    monkeypatch.setattr(security, "get_sql_session", _session)


def test_active_account_token_still_authenticates(monkeypatch):
    _sql_backend(monkeypatch, [("user-active", 0)])
    assert get_current_user_id(_creds(create_access_token("user-active"))) == "user-active"


def test_deleted_account_token_is_rejected(monkeypatch):
    _sql_backend(monkeypatch, [("user-gone", 1)])
    with pytest.raises(HTTPException) as exc:
        get_current_user_id(_creds(create_access_token("user-gone")))
    assert exc.value.status_code == 401


def test_token_for_nonexistent_account_is_rejected(monkeypatch):
    _sql_backend(monkeypatch, [("user-active", 0)])
    with pytest.raises(HTTPException) as exc:
        get_current_user_id(_creds(create_access_token("user-phantom")))
    assert exc.value.status_code == 401


def test_deleted_account_cannot_pass_as_another_active_account(monkeypatch):
    _sql_backend(monkeypatch, [("user-gone", 1), ("user-active", 0)])
    with pytest.raises(HTTPException):
        get_current_user_id(_creds(create_access_token("user-gone")))
    assert get_current_user_id(_creds(create_access_token("user-active"))) == "user-active"


def test_missing_credentials_still_rejected(monkeypatch):
    _sql_backend(monkeypatch, [("user-active", 0)])
    with pytest.raises(HTTPException) as exc:
        get_current_user_id(None)
    assert exc.value.status_code == 401


def test_supabase_path_rejects_deleted_account(monkeypatch):
    monkeypatch.setattr(security, "has_sql", lambda: False)
    table = MagicMock()
    table.select.return_value = table
    table.eq.return_value = table
    table.limit.return_value = table
    table.execute.return_value = SimpleNamespace(data=[{"is_deleted": True}])
    monkeypatch.setattr(security, "get_db", lambda: SimpleNamespace(table=lambda name: table))
    with pytest.raises(HTTPException) as exc:
        get_current_user_id(_creds(create_access_token("user-gone")))
    assert exc.value.status_code == 401


def test_backend_failure_fails_closed(monkeypatch):
    monkeypatch.setattr(security, "has_sql", lambda: True)
    @contextmanager
    def _broken():
        raise RuntimeError("db down")
        yield
    monkeypatch.setattr(security, "get_sql_session", _broken)
    with pytest.raises(RuntimeError):
        get_current_user_id(_creds(create_access_token("user-active")))


def test_refresh_rejects_deleted_account(monkeypatch):
    import app.api.auth as auth_api

    rows = [("user-gone", 1), ("user-active", 0)]
    from sqlalchemy.pool import StaticPool
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    with engine.begin() as setup:
        setup.execute(text("CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT, is_deleted INTEGER)"))
        for uid, deleted in rows:
            setup.execute(text("INSERT INTO users (id, email, is_deleted) VALUES (:id, :e, :d)"), {"id": uid, "e": uid + "@example.test", "d": deleted})

    @contextmanager
    def _session():
        connection = engine.connect()
        try:
            yield connection
        finally:
            connection.close()

    monkeypatch.setattr(auth_api, "has_sql", lambda: True)
    monkeypatch.setattr(auth_api, "get_sql_session", _session)
    request = SimpleNamespace(headers={})

    payload = SimpleNamespace(refresh_token=create_refresh_token("user-gone"))
    with pytest.raises(HTTPException) as exc:
        auth_api.refresh_token(request, payload)
    assert exc.value.status_code == 401


def test_refresh_still_issues_for_active_account(monkeypatch):
    import app.api.auth as auth_api

    from sqlalchemy.pool import StaticPool
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    with engine.begin() as setup:
        setup.execute(text("CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT, is_deleted INTEGER)"))
        setup.execute(text("INSERT INTO users (id, email, is_deleted) VALUES ('user-active', 'a@example.test', 0)"))

    @contextmanager
    def _session():
        connection = engine.connect()
        try:
            yield connection
        finally:
            connection.close()

    monkeypatch.setattr(auth_api, "has_sql", lambda: True)
    monkeypatch.setattr(auth_api, "get_sql_session", _session)
    request = SimpleNamespace(headers={})
    payload = SimpleNamespace(refresh_token=create_refresh_token("user-active"))
    res = auth_api.refresh_token(request, payload)
    assert res.access_token
