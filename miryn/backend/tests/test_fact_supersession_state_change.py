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
    return {"entity": entity, "attribute": "status", "old_value": old, "new_value": new}


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


def test_two_employment_facts_both_match_means_no_link():
    rows = [_cand("Works at Acme Corp as a designer"), _cand("Acme Corp manager is Dana")]
    assert select_supersede_candidate(rows, NEW, _marker("Acme", "Acme Corp", "laid off")) is None


def test_manual_memory_is_never_superseded_by_state_change():
    old = _cand("Works at Acme Corp", extractor="manual")
    assert select_supersede_candidate([old], NEW, _marker("Acme", "Acme Corp", "laid off")) is None


def test_newer_fact_is_not_superseded_by_older_marker():
    old = _cand("Works at Acme Corp", days=-1)
    assert select_supersede_candidate([old], NEW, _marker("Acme", "Acme Corp", "laid off")) is None
