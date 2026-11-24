from app.services.importance import score_message_heuristic


def test_unpunctuated_question_is_not_stored_as_fact():
    assert score_message_heuristic("what is my manager name and where do i work") == []
    assert score_message_heuristic("where do i live") == []


def test_statements_and_punctuated_questions_unchanged():
    assert score_message_heuristic("my manager is Dev and I work at a design agency")
    assert score_message_heuristic("I live in Pune and I work at a design agency")
    assert score_message_heuristic("Where do I work and who is my manager?") == []
