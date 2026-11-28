"""A deleted conversation cannot re-enter the model's context.

Conversation delete is a soft delete (is_deleted). Entry validation must
treat a deleted conversation as gone: posting to it would otherwise let its
history flow into the reply prompt through recent_turns. Cross-user access
stays denied either way.
"""
from contextlib import contextmanager

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text

import app.api.chat as chat_api


def _session_factory(connection):
    @contextmanager
    def _get_sql_session():
        yield connection
    return _get_sql_session


@pytest.fixture
def conn(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE conversations (id TEXT PRIMARY KEY, user_id TEXT, is_deleted INTEGER)"
        ))
        connection.execute(text(
            "INSERT INTO conversations (id, user_id, is_deleted) VALUES "
            "('c-live', 'u1', 0), ('c-deleted', 'u1', 1)"
        ))
        monkeypatch.setattr(chat_api, "has_sql", lambda: True)
        monkeypatch.setattr(chat_api, "get_sql_session", _session_factory(connection))
        yield connection


def test_live_conversation_passes_for_owner(conn):
    chat_api._validate_conversation_owner("c-live", "u1")


def test_deleted_conversation_is_not_found_for_owner(conn):
    with pytest.raises(HTTPException) as exc:
        chat_api._validate_conversation_owner("c-deleted", "u1")
    assert exc.value.status_code == 404


def test_cross_user_remains_forbidden(conn):
    with pytest.raises(HTTPException) as exc:
        chat_api._validate_conversation_owner("c-live", "u2")
    assert exc.value.status_code == 403


def test_missing_conversation_is_not_found(conn):
    with pytest.raises(HTTPException) as exc:
        chat_api._validate_conversation_owner("c-nope", "u1")
    assert exc.value.status_code == 404
