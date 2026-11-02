"""Known facts in the prompt carry statement dates so the
"most recent statement wins" rule has chronology to work with.

Dict rows from FactStore.list_top (created_at/last_seen_at) get a
"[stated YYYY-MM-DD]" prefix; plain strings pass through unchanged, and
dicts without timestamps fall back to a bare bullet.
"""
from datetime import datetime

from app.services.llm_service import LLMService


def _format(facts):
    return LLMService()._format_context({"known_facts": facts, "memories": []})


def test_dict_facts_get_stated_date_prefix():
    facts = [
        {"content": "Training for a triathlon in Goa on December 14",
         "created_at": datetime(2026, 10, 20, 10, 0, 0), "last_seen_at": None},
        {"content": "Training for a triathlon in Goa on January 11",
         "created_at": datetime(2026, 10, 28, 10, 0, 0), "last_seen_at": datetime(2026, 10, 28, 12, 0, 0)},
    ]
    out = _format(facts)
    assert "- [stated 2026-10-20] Training for a triathlon in Goa on December 14" in out
    assert "- [stated 2026-10-28] Training for a triathlon in Goa on January 11" in out


def test_last_seen_at_wins_over_created_at():
    facts = [{"content": "User's dog is allergic to chicken",
              "created_at": datetime(2026, 10, 10, 10, 0, 0),
              "last_seen_at": datetime(2026, 10, 25, 9, 0, 0)}]
    assert "- [stated 2026-10-25] User's dog is allergic to chicken" in _format(facts)


def test_string_facts_pass_through_unchanged():
    out = _format(["Training for a triathlon in Goa on December 14"])
    assert "- Training for a triathlon in Goa on December 14" in out
    assert "[stated" not in out


def test_dict_fact_without_timestamp_falls_back_to_bare_bullet():
    out = _format([{"content": "User's dog is allergic to chicken"}])
    assert "- User's dog is allergic to chicken" in out
    assert "[stated" not in out
