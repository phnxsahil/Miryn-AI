from app.services.importance import clean_fact_text, score_message_heuristic


def test_identity_fact_scores_high():
    facts = score_message_heuristic("My name is Sahil and I'm 22")
    assert facts and facts[0].category == "identity"
    assert facts[0].importance >= 0.85


def test_relationship_fact_scores_high():
    facts = score_message_heuristic("my sister Anya is getting married in June")
    assert facts and facts[0].category == "relationship"
    assert facts[0].importance >= 0.8


def test_goal_fact_scores_high():
    facts = score_message_heuristic("I want to quit my job and start a company")
    assert facts and facts[0].category == "goal"
    assert facts[0].importance >= 0.75


def test_emotional_event_scores_high():
    facts = score_message_heuristic("I'm devastated, my grandfather passed away")
    assert facts and facts[0].importance >= 0.85
    assert facts[0].emotional_weight >= 0.6


def test_chitchat_is_not_stored():
    for message in ("ok", "thanks!", "lol", "what's the weather?", "can you explain recursion?"):
        facts = score_message_heuristic(message)
        assert not facts or all(fact.importance < 0.3 for fact in facts)


def test_clean_fact_text_rewrites_clauses():
    assert clean_fact_text("Hi, I just moved to Pune for college and I am nervous") == "Moved to Pune for college; feels nervous"


def test_clean_fact_text_common_verb():
    assert clean_fact_text("I love hiking on weekends") == "Loves hiking on weekends"


def test_clean_fact_text_preserves_names_and_months():
    text = clean_fact_text("My sister Riya is getting married in June")
    assert "Riya" in text and "June" in text and text.startswith("Their sister")


def test_clean_fact_text_short_input_is_unchanged():
    assert clean_fact_text("ok") == "ok"


def test_clean_text_is_used_for_scored_facts():
    facts = score_message_heuristic("Hi, I just moved to Pune for college and I am nervous")
    assert facts[0].text == "Moved to Pune for college; feels nervous"
