from app.services.importance import make_conversation_title


def test_title_cleans_first_person_sentence():
    assert make_conversation_title("Hi, I just moved to Pune for college and I am nervous") == "Moved to Pune for college"


def test_title_keeps_questions_without_question_mark():
    assert make_conversation_title("How do I start running?") == "How do I start running"


def test_title_empty_is_new_chat():
    assert make_conversation_title("   ") == "New chat"


def test_title_truncates_at_word_boundary():
    title = make_conversation_title("A " + "very long message " * 20)
    assert len(title) <= 41
    assert not title.endswith(" …")
