"""False-positive correction markers must die at the deterministic gates.

The LLM marker path is unmeasured (see PR body, Measurement gap), so these
tests assume a HALLUCINATING model: plausible-looking but wrong `corrects`
payloads. Every one must resolve to no link, leaving every fact active. This
is the defense-in-depth that lets the feature ship dark: a bad marker alone
can never hide a memory.
"""

from datetime import datetime, timedelta

from app.services.fact_store import select_supersede_candidate

BASE = datetime(2026, 10, 31, 6, 0, 0)


def _fact(text, category="goal", extractor="llm", age_hours=2):
    return {
        "id": f"id-{abs(hash(text)) % 100000}",
        "text": text,
        "category": category,
        "extractor": extractor,
        "created_at": BASE - timedelta(hours=age_hours),
    }


NEW = {"category": "goal", "created_at": BASE}


def test_marker_with_non_dict_payload_is_ignored():
    old = _fact("Training for a triathlon in Goa on December 14")
    assert select_supersede_candidate([old], NEW, "December 14->January 11") is None


def test_marker_missing_attribute_is_ignored():
    old = _fact("Training for a triathlon in Goa on December 14")
    bad = {"entity": "Goa triathlon", "old_value": "December 14", "new_value": "January 11"}
    assert select_supersede_candidate([old], NEW, bad) is None


def test_stopword_only_entity_is_ignored():
    old = _fact("Training for a triathlon in Goa on December 14")
    bad = {"entity": "the", "attribute": "date", "old_value": "December 14", "new_value": "January 11"}
    assert select_supersede_candidate([old], NEW, bad) is None


def test_old_value_alone_cannot_select_unrelated_fact():
    # Entity matches nothing; old_value tokens appear in an unrelated fact.
    old = _fact("Visiting my parents on December 14")
    bad = {"entity": "Goa triathlon", "attribute": "date",
           "old_value": "December 14", "new_value": "January 11"}
    assert select_supersede_candidate([old], NEW, bad) is None


def test_entity_alone_cannot_select_fact_with_different_value():
    # Entity matches; the claimed old value does not appear in the fact.
    old = _fact("Training for a triathlon in Goa on March 3")
    bad = {"entity": "Goa triathlon", "attribute": "date",
           "old_value": "December 14", "new_value": "January 11"}
    assert select_supersede_candidate([old], NEW, bad) is None


def test_two_plausible_targets_mean_no_link():
    # A hallucinated marker that matches two different facts must not pick one.
    rows = [
        _fact("Training for a triathlon in Goa on December 14"),
        _fact("The Goa triathlon happens December 14", age_hours=5),
    ]
    bad = {"entity": "Goa triathlon", "attribute": "date",
           "old_value": "December 14", "new_value": "January 11"}
    assert select_supersede_candidate(rows, NEW, bad) is None


def test_case_variant_identical_values_are_not_a_correction():
    old = _fact("Training for a triathlon in Goa on December 14")
    bad = {"entity": "Goa triathlon", "attribute": "date",
           "old_value": "december 14", "new_value": "  December 14 "}
    assert select_supersede_candidate([old], NEW, bad) is None


def test_preference_flip_marker_still_needs_a_matching_fact():
    # Polarity flip is present and valid, but no stored fact matches -
    # the marker must still not create a link out of nothing.
    corrects = {"entity": "coriander", "attribute": "food preference",
                "old_value": "hate coriander", "new_value": "like coriander",
                "polarity_old": "negative", "polarity_new": "positive"}
    new_pref = {"category": "preference", "created_at": BASE}
    unrelated = _fact("Allergic to peanuts since childhood", category="preference")
    assert select_supersede_candidate([unrelated], new_pref, corrects) is None
