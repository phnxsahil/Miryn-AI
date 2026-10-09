from app.services.importance import clean_fact_text, score_message_heuristic
from app.config import settings


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


def test_additional_durable_facts_are_captured_and_cleaned():
    cases = (
        ("I am training for a half marathon in March", "Training for a half marathon in March"),
        ("I have trouble sleeping before exams", "Has trouble sleeping before exams"),
        ("I started dating someone named Aarav", "Started dating someone named Aarav"),
        ("I quit smoking 12 days ago", "Quit smoking 12 days ago"),
        ("I am vegetarian and allergic to peanuts", "Is vegetarian; allergic to peanuts"),
        ("My birthday is on 14 March", "Birthday is 14 March"),
        ("I feel anxious about money lately", "Feels anxious about money"),
        ("I am TERRIBLY stressed about the visa interview", "Feels TERRIBLY stressed about the visa interview"),
    )
    for sentence, expected in cases:
        facts = score_message_heuristic(sentence)
        assert facts, sentence
        assert facts[0].importance >= settings.IMPORTANCE_CORE_THRESHOLD * 0.8, sentence
        assert expected.lower() in facts[0].text.lower(), (sentence, facts[0].text)


def test_added_capture_rules_keep_existing_examples_and_skip_chitchat():
    existing = (
        "I moved to Pune for college", "I live in Pune", "My goal is to learn Rust",
        "My dog Bruno is sick", "I got promoted today!!!", "My sister Riya is getting married in June",
        "I love hiking on weekends",
    )
    for sentence in existing:
        assert score_message_heuristic(sentence), sentence
    for sentence in ("ok", "thanks!", "lol", "What should I cook tonight?", "I had a sandwich"):
        assert not score_message_heuristic(sentence), sentence


def test_work_and_manager_clauses_clean_separately():
    assert clean_fact_text("I work at a startup and my manager keeps changing deadlines") == "Works at a startup; their manager keeps changing deadlines"
