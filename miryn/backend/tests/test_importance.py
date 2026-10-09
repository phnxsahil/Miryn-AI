from app.services.importance import score_message_heuristic


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
