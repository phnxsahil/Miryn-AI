from app.services.importance import make_conversation_title


def test_title_keeps_the_user_message():
    assert make_conversation_title("I am vegetarian and allergic to peanuts") == "I am vegetarian and allergic to peanuts"


def test_title_keeps_questions_without_question_mark():
    assert make_conversation_title("How do I start running?") == "How do I start running"


def test_title_empty_is_new_chat():
    assert make_conversation_title("   ") == "New chat"


def test_title_short_message_is_new_chat():
    assert make_conversation_title("ok") == "New chat"


def test_title_truncates_at_word_boundary():
    title = make_conversation_title("a" * 100)
    assert len(title) <= 41
    assert title.endswith("…")
