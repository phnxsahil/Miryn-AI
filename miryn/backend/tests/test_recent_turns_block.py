"""Offline assembly checks with fictional rows. They do NOT evaluate model behaviour."""
from app.services.recent_turns import build_recent_turns_block as build


def _rows(n):
    return [{"role": "user" if i % 2 == 0 else "assistant", "content": f"turn {i}"} for i in range(n)]


def test_order_and_labels():
    out = build(_rows(3))
    assert out.splitlines()[1:] == ["User: turn 0", "Miryn: turn 1", "User: turn 2"]


def test_keeps_newest_turns_under_turn_limit():
    out = build(_rows(20), max_turns=4)
    assert "turn 19" in out and "turn 16" in out and "turn 15" not in out


def test_long_newest_turn_is_kept_and_older_dropped_whole():
    rows = [{"role": "user", "content": "short"}, {"role": "user", "content": "x" * 5000}]
    out = build(rows, max_chars=100)
    assert "short" not in out and out.endswith("…")


def test_skips_unknown_roles_and_empty():
    assert build([{"role": "system", "content": "s"}, {"role": "user", "content": "  "}]) == ""
