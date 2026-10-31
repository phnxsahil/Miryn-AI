"""Recall questions and request probes must not be stored as facts.

Regression tests for the live bug where "What's my sister's name again?"
and "Without scrolling, list: my race..." were stored as memories, while
real assertions embedded inside questions must still be captured.
"""

from app.services.importance import score_message_heuristic


def test_pure_recall_question_is_not_stored():
    assert not score_message_heuristic("What's my sister's name again? You should know this.")


def test_imperative_recall_request_is_not_stored():
    assert not score_message_heuristic(
        "Without scrolling, list: my race and its date, what I'm currently saving for; their pet's name."
    )


def test_direct_probe_question_is_not_stored():
    assert not score_message_heuristic("Do I have any pets?")


def test_no_hints_probe_is_not_stored():
    assert not score_message_heuristic("Quick check, no hints: what fitness goal am I currently working toward?")


def test_assertion_inside_question_is_kept():
    facts = score_message_heuristic("Given that my dog Biscuit is allergic to chicken, what food should I buy?")
    assert facts, "embedded durable assertion should be captured"
    assert any("allergic to chicken" in fact.text.lower() for fact in facts), [f.text for f in facts]


def test_assertion_before_opinion_question_is_kept():
    facts = score_message_heuristic("I hate coriander in every dish, what do you think?")
    assert facts and any("coriander" in fact.text.lower() for fact in facts), [f.text for f in facts]


def test_plain_assertions_unaffected():
    facts = score_message_heuristic("I'm training for a triathlon in Goa on December 14.")
    assert facts and any("triathlon" in fact.text.lower() for fact in facts)


def test_do_you_probe_is_not_stored():
    assert not score_message_heuristic("Do you remember my sister's name?")


def test_did_you_probe_is_not_stored():
    assert not score_message_heuristic("Did you save my flight number?")


def test_should_you_probe_is_not_stored():
    assert not score_message_heuristic("Should you know my dog's name by now?")


def test_guess_probe_is_not_stored():
    assert not score_message_heuristic("Guess what my dog's name is.")


def test_mixed_statement_probe_stores_no_question():
    # The trailing clause is a question even though the sentence opens with a
    # statement; the whole message is a recall probe and nothing is stored.
    assert not score_message_heuristic("Given that the meeting moved to Friday, what's on my calendar?")


def test_hypothetical_lead_without_question_mark_is_not_stored():
    assert not score_message_heuristic("What if I quit my job.")


def test_hypothetical_lead_with_question_mark_is_not_stored():
    assert not score_message_heuristic("What if I moved to Pune next year?")


def test_lets_say_hypothetical_is_not_stored():
    assert not score_message_heuristic("Let's say I stopped drinking coffee, what would change?")
