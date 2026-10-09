from sqlalchemy import create_engine, text

from app.api.chat import _select_history_page


def test_history_pages_return_latest_messages_then_older_messages_in_order():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE messages (id TEXT PRIMARY KEY, conversation_id TEXT, role TEXT, content TEXT, created_at TEXT)"
        ))
        connection.execute(
            text("INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (:id, 'c1', 'user', :id, :created_at)"),
            [{"id": f"m{i:03d}", "created_at": f"2026-01-01T00:00:{i:03d}"} for i in range(120)],
        )

    with engine.connect() as connection:
        first, has_more = _select_history_page(connection, "c1", 50, None)
        second, has_more_2 = _select_history_page(connection, "c1", 50, first[0]["id"])
        third, has_more_3 = _select_history_page(connection, "c1", 50, second[0]["id"])

    assert [row["id"] for row in first] == [f"m{i:03d}" for i in range(70, 120)]
    assert [row["id"] for row in second] == [f"m{i:03d}" for i in range(20, 70)]
    assert [row["id"] for row in third] == [f"m{i:03d}" for i in range(20)]
    assert (has_more, has_more_2, has_more_3) == (True, True, False)
