from app.services.open_loop_parse import MAX_LOOPS_PER_CHAT, parse_open_loops


def test_valid_items_are_kept_with_clamped_importance():
    out = parse_open_loops([{"topic": "Decide on Pune move", "importance": 3}, {"topic": "Reply to recruiter", "importance": 9}])
    assert out == [
        {"topic": "Decide on Pune move", "importance": 3},
        {"topic": "Reply to recruiter", "importance": 3},
    ]


def test_plain_strings_and_non_lists_are_not_open_loops():
    assert parse_open_loops(["dog food", "fintech"]) == []
    assert parse_open_loops(None) == []
    assert parse_open_loops({"topic": "x"}) == []
    assert parse_open_loops("nope") == []


def test_malformed_items_are_skipped_and_defaults_apply():
    out = parse_open_loops([
        {"topic": "  "},
        {"importance": 2},
        {"topic": 5},
        {"topic": "Book flight", "importance": "high"},
        {"topic": "book  flight"},
    ])
    assert out == [{"topic": "Book flight", "importance": 1}]


def test_cap_per_chat_and_topic_length():
    raw = [{"topic": f"t{i}"} for i in range(10)]
    assert len(parse_open_loops(raw)) == MAX_LOOPS_PER_CHAT
    assert len(parse_open_loops([{"topic": "x" * 500}])[0]["topic"]) == 80
