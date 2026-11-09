"""Only the user's own current statements become durable facts (offline, stubbed LLM)."""

import asyncio
import json

from app.services.importance import score_message, score_message_llm


class _StubLLM:
    provider = "openai"
    client = object()

    def __init__(self, payload):
        self._payload = payload

    async def generate(self, prompt, max_tokens=400):
        self.prompt = prompt
        return json.dumps(self._payload)

    def parse_json_response(self, response):
        return json.loads(response)


def _fact(text, source=None, corrects=None, importance=0.85):
    item = {"fact": text, "category": "life_event", "importance": importance,
            "emotional_weight": 0.2, "corrects": corrects}
    if source is not None:
        item["source"] = source
    return item


_CORRECTS = {"entity": "race", "attribute": "date", "old_value": "December 14", "new_value": "January 11"}


def _run(items):
    llm = _StubLLM({"facts": items})
    return asyncio.run(score_message_llm(llm, "fictional message")), llm


def test_self_current_fact_and_marker_kept():
    facts, _ = _run([_fact("race is January 11", "self_current", _CORRECTS)])
    assert len(facts) == 1 and facts[0].corrects["new_value"] == "January 11"


def test_quoted_hypothetical_third_party_are_not_stored():
    facts, _ = _run([
        _fact("race is January 11", "quoted", _CORRECTS),
        _fact("might move to Pune", "hypothetical"),
        _fact("I am vegetarian", "self_current", importance=0.6),
    ])
    assert [f.text for f in facts] == ["I am vegetarian"]
    assert facts[0].corrects is None


def test_missing_source_keeps_fact_but_never_a_correction_marker():
    facts, _ = _run([_fact("race is January 11", None, _CORRECTS)])
    assert len(facts) == 1 and facts[0].corrects is None


def test_prompt_declares_source_values():
    _, llm = _run([_fact("I am vegetarian", "self_current", importance=0.6)])
    for value in ("self_current", "quoted", "hypothetical", "third_party"):
        assert value in llm.prompt


def test_all_non_self_facts_return_empty_without_heuristic_fallback(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "IMPORTANCE_USE_LLM", True)
    llm = _StubLLM({"facts": [_fact("my friend quit her job", "third_party")]})
    assert asyncio.run(score_message(llm, "My friend said I quit my job")) == []
