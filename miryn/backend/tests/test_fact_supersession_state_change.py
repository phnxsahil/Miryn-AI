"""Implicit state changes (job loss, moving) use the same fail-closed resolver.

Fictional data only. These test the deterministic linking, not the LLM marker.
"""

from datetime import datetime, timedelta

from app.services.fact_store import select_supersede_candidate

BASE = datetime(2026, 11, 24, 12, 0, 0)


def _cand(text, category="work_career", extractor="llm", days=5):
    return {
        "id": f"id-{abs(hash(text)) % 100000}",
        "text": text,
        "category": category,
        "extractor": extractor,
        "created_at": BASE - timedelta(days=days),
    }


NEW = {"category": "work_career", "created_at": BASE}


def _marker(entity, old, new):
    return {"entity": entity, "attribute": "status", "old_value": old, "new_value": new, "kind": "state_change"}


def test_job_loss_supersedes_the_single_matching_employment_fact():
    old = _cand("Works at Acme Corp as a designer")
    chosen = select_supersede_candidate([old], NEW, _marker("Acme", "works at Acme Corp", "laid off from Acme"))
    assert chosen == old


def test_move_supersedes_single_city_fact():
    old = _cand("Lives in Pune", category="life_event")
    new = {"category": "life_event", "created_at": BASE}
    chosen = select_supersede_candidate([old], new, _marker("home city", "lives in Pune", "moved to Goa"))
    assert chosen is None  # entity "home city" is not in the old fact text: fail closed


def test_move_with_entity_in_old_text_is_linked():
    old = _cand("Lives in Pune", category="life_event")
    new = {"category": "life_event", "created_at": BASE}
    chosen = select_supersede_candidate([old], new, _marker("lives", "Pune", "Goa"))
    assert chosen == old


def test_two_user_employment_facts_both_match_means_no_link():
    rows = [_cand("Works at Acme Corp as a designer"), _cand("Freelances for Acme Corp on weekends")]
    assert select_supersede_candidate(rows, NEW, _marker("Acme", "Acme Corp", "laid off")) is None


def test_third_party_match_makes_it_ambiguous_so_nothing_is_superseded():
    mine, theirs = _cand("Works at Acme Corp as a designer"), _cand("Acme Corp manager is Dana")
    assert select_supersede_candidate([mine, theirs], NEW, _marker("Acme", "Acme Corp", "laid off")) is None


def test_manual_memory_is_never_superseded_by_state_change():
    old = _cand("Works at Acme Corp", extractor="manual")
    assert select_supersede_candidate([old], NEW, _marker("Acme", "Acme Corp", "laid off")) is None


def test_newer_fact_is_not_superseded_by_older_marker():
    old = _cand("Works at Acme Corp", days=-1)
    assert select_supersede_candidate([old], NEW, _marker("Acme", "Acme Corp", "laid off")) is None


# Markers below are the shape the extractor produced in a fictional check: it
# sees only the new message, so entity/old_value are inferred, not copied from
# the stored fact. The resolver must still match only when words line up.

def test_inferred_old_value_work_at_acme_matches_stored_works_at():
    old = _cand("Works at Acme Corp as a designer")
    marker = {"entity": "Acme", "attribute": "employment", "old_value": "work at Acme", "new_value": "laid off from Acme", "kind": "state_change"}
    assert select_supersede_candidate([old], NEW, marker) == old


def test_inferred_old_value_does_not_match_a_different_employer():
    old = _cand("Works at Zephyr Labs as a designer")
    marker = {"entity": "Acme", "attribute": "employment", "old_value": "work at Acme", "new_value": "laid off from Acme", "kind": "state_change"}
    assert select_supersede_candidate([old], NEW, marker) is None


def test_third_party_acme_fact_alongside_users_makes_it_ambiguous():
    rows = [_cand("Works at Acme Corp as a designer"), _cand("Friend Dana works at Acme")]
    marker = {"entity": "Acme", "attribute": "employment", "old_value": "work at Acme", "new_value": "laid off from Acme", "kind": "state_change"}
    assert select_supersede_candidate(rows, NEW, marker) is None


def test_different_category_fact_is_untouched():
    old = _cand("Works at Acme Corp", category="relationship")
    marker = {"entity": "Acme", "attribute": "employment", "old_value": "work at Acme", "new_value": "laid off from Acme", "kind": "state_change"}
    assert select_supersede_candidate([old], NEW, marker) is None


def test_negated_new_value_equal_to_old_is_ignored():
    old = _cand("Works at Acme Corp")
    marker = {"entity": "Acme", "attribute": "employment", "old_value": "works at Acme", "new_value": "Works at Acme", "kind": "state_change"}
    assert select_supersede_candidate([old], NEW, marker) is None


import pytest


def test_lone_third_party_fact_is_not_superseded():
    old = _cand("Friend Dana works at Acme")
    marker = {"entity": "Acme", "attribute": "employment", "old_value": "work at Acme", "new_value": "laid off from Acme", "kind": "state_change"}
    assert select_supersede_candidate([old], NEW, marker) is None


@pytest.mark.parametrize(
    "text",
    [
        "Dana works at Acme",
        "dana works at Acme",
        "Zubin Raghunathan works at Acme",
        "Priya has a job at Acme",
        "Friend Dana works at Acme",
        "Her brother works at Acme",
        "Manager at Acme is Rohan",
        "Acme employs Dana",
        "Said \"I work at Acme\"",
        "Works at Acme with his brother",
    ],
)
def test_facts_about_other_people_are_never_superseded(text):
    marker = {"entity": "Acme", "attribute": "employment", "old_value": "work at Acme", "new_value": "laid off from Acme", "kind": "state_change"}
    assert select_supersede_candidate([_cand(text)], NEW, marker) is None


@pytest.mark.parametrize("text", ["Works at Acme", "Started work at Acme", "The user works at Acme as a designer", "Is working at Acme"])
def test_user_facts_with_implied_subject_still_supersede(text):
    old = _cand(text)
    marker = {"entity": "Acme", "attribute": "employment", "old_value": "work at Acme", "new_value": "laid off from Acme", "kind": "state_change"}
    assert select_supersede_candidate([old], NEW, marker) == old


def test_state_change_with_unfamiliar_opening_word_is_left_unchanged():
    old = _cand("Employer is Acme")
    assert select_supersede_candidate([old], NEW, _marker("Acme", "Acme", "laid off")) is None


def test_explicit_correction_path_keeps_working_without_the_kind_flag():
    old = _cand("Employer is Acme")
    marker = {"entity": "Employer", "attribute": "name", "old_value": "Acme", "new_value": "Zephyr"}
    assert select_supersede_candidate([old], NEW, marker) == old


def test_parse_corrects_keeps_only_the_state_change_kind():
    from app.services.importance import _parse_corrects

    base = {"entity": "Acme", "attribute": "employment", "old_value": "works at Acme", "new_value": "laid off"}
    assert _parse_corrects({**base, "kind": "state_change"})["kind"] == "state_change"
    assert "kind" not in _parse_corrects({**base, "kind": "anything else"})
