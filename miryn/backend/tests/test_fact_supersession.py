"""Explicit-correction linking: deterministic resolver behavior.

Only an explicit, typed correction (entity + attribute + old value + new
value) may supersede an existing fact, and only when exactly one eligible
candidate matches. Everything else stays active and visible.
"""

from datetime import datetime, timedelta

from app.services.fact_store import FactStore, select_supersede_candidate

BASE = datetime(2026, 10, 31, 6, 0, 0)


def _cand(text, category="goal", extractor="llm", age_hours=2):
    return {
        "id": f"id-{abs(hash(text)) % 100000}",
        "text": text,
        "category": category,
        "extractor": extractor,
        "created_at": BASE - timedelta(hours=age_hours),
    }


CORRECTS = {
    "entity": "Goa triathlon",
    "attribute": "date",
    "old_value": "December 14",
    "new_value": "January 11",
    "polarity_old": "neutral",
    "polarity_new": "neutral",
}

NEW_FACT = {"category": "goal", "created_at": BASE}


def test_unique_matching_candidate_is_selected():
    old = _cand("Training for a triathlon in Goa on December 14")
    chosen = select_supersede_candidate([old], NEW_FACT, CORRECTS)
    assert chosen == old


def test_no_candidate_means_no_link():
    chosen = select_supersede_candidate([_cand("Physio advised keeping runs under 10 km")], NEW_FACT, CORRECTS)
    assert chosen is None


def test_multiple_candidates_mean_no_link():
    rows = [
        _cand("Training for a triathlon in Goa on December 14"),
        _cand("The Goa triathlon happens December 14", age_hours=5),
    ]
    assert select_supersede_candidate(rows, NEW_FACT, CORRECTS) is None


def test_manual_memory_is_never_a_target():
    old = _cand("Training for a triathlon in Goa on December 14", extractor="manual")
    assert select_supersede_candidate([old], NEW_FACT, CORRECTS) is None


def test_category_mismatch_means_no_link():
    old = _cand("Training for a triathlon in Goa on December 14", category="health")
    assert select_supersede_candidate([old], NEW_FACT, CORRECTS) is None


def test_newer_candidate_is_never_a_target():
    old = _cand("Training for a triathlon in Goa on December 14", age_hours=-1)
    assert select_supersede_candidate([old], NEW_FACT, CORRECTS) is None


def test_entity_mismatch_means_no_link():
    old = _cand("Training for a marathon in Pune on December 14")
    assert select_supersede_candidate([old], NEW_FACT, CORRECTS) is None


def test_identical_old_and_new_value_is_not_a_correction():
    bad = dict(CORRECTS, new_value="December 14")
    old = _cand("Training for a triathlon in Goa on December 14")
    assert select_supersede_candidate([old], NEW_FACT, bad) is None


def test_stance_correction_matches_with_prefix_tolerance():
    corrects = {
        "entity": "coriander",
        "attribute": "food preference",
        "old_value": "hate coriander",
        "new_value": "like coriander",
        "polarity_old": "negative",
        "polarity_new": "positive",
    }
    new_fact = {"category": "preference", "created_at": BASE}
    old = _cand("Hates coriander", category="preference")
    assert select_supersede_candidate([old], new_fact, corrects) == old


def test_link_returns_empty_without_sql(monkeypatch):
    monkeypatch.setattr("app.services.fact_store.has_sql", lambda: False)
    fact = type("F", (), {"corrects": CORRECTS, "text": "x", "category": "goal"})()
    assert FactStore().link_explicit_corrections("user-1", [fact], "msg-1") == []


def test_facts_without_corrections_are_ignored():
    fact = type("F", (), {"corrects": None, "text": "x", "category": "goal"})()
    assert FactStore().link_explicit_corrections("user-1", [fact], "msg-1") == []
