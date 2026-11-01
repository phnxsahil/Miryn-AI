"""Characterization tests for how MemoryLayer merges candidate lists and scores them.

Offline and deterministic: the four searches are stubbed with fixed lists, so these test the MECHANICS in
memory_layer.py (candidate limits, recency only from the temporal list, transient messages taking slots).
They say nothing about real Gemini embedding quality or real ranking performance.
Where a test pins current behavior that may be a product problem, its name says "characterization".
"""
import asyncio
import logging
import math
from datetime import datetime, timedelta

import pytest

from app.services.memory_layer import MemoryLayer


def _ago(days):
    return (datetime.utcnow() - timedelta(days=days, hours=1)).isoformat()


def _msg(i, days=0, sim=None, imp=0.5, text=None):
    m = {"id": i, "content": text or i, "created_at": _ago(days), "importance_score": imp}
    if sim is not None:
        m["similarity"] = sim
    return m


class _Cache:
    def get(self, k): return None
    def setex(self, *a, **k): pass
    def sadd(self, *a, **k): pass
    def expire(self, *a, **k): pass


class _Embedder:
    def embed(self, text): return [0.0]


def _layer(monkeypatch, transient=(), semantic=(), temporal=(), important=()):
    ml = MemoryLayer.__new__(MemoryLayer)
    ml.cache, ml.embedder, ml.logger, ml.episodic_days = _Cache(), _Embedder(), logging.getLogger("t"), 7
    seen = {}
    monkeypatch.setattr(ml, "_transient_search", lambda u, c, limit: (seen.__setitem__("transient", limit), list(transient))[1])
    monkeypatch.setattr(ml, "_semantic_search", lambda u, e, limit, sql_session=None: (seen.__setitem__("semantic", limit), list(semantic))[1])
    monkeypatch.setattr(ml, "_temporal_search", lambda u, days, limit, sql_session=None: (seen.__setitem__("temporal", (days, limit)), list(temporal))[1])
    monkeypatch.setattr(ml, "_importance_search", lambda u, threshold, limit, sql_session=None: (seen.__setitem__("important", (threshold, limit)), list(important))[1])
    ml.seen = seen
    return ml


def _ids(r): return [m["id"] for m in r]


def test_candidate_limits_and_windows_match_source(monkeypatch):
    ml = _layer(monkeypatch)
    asyncio.run(ml.retrieve_context("u", "q", limit=5))
    assert ml.seen["transient"] == 10 and ml.seen["semantic"] == 15
    assert ml.seen["temporal"] == (7, 15) and ml.seen["important"] == (0.7, 15)


def test_weights_and_recency_formula():
    ml = MemoryLayer.__new__(MemoryLayer)
    both = {**_msg("a", days=2, sim=0.8, imp=0.6)}
    out = ml._hybrid_score([both], [_msg("a", days=2, imp=0.6)], [])
    rec = math.exp(-0.1 * 2)   # created 2 days + 1 hour ago -> .days == 2
    assert out[0]["hybrid_score"] == pytest.approx(0.5 * 0.8 + 0.3 * rec + 0.2 * 0.6)


def test_semantic_only_candidate_gets_zero_recency():
    ml = MemoryLayer.__new__(MemoryLayer)
    out = ml._hybrid_score([_msg("old", days=40, sim=0.8, imp=0.5)], [], [])
    assert out[0]["recency_score"] == 0 and out[0]["hybrid_score"] == pytest.approx(0.5 * 0.8 + 0.2 * 0.5)


def test_temporal_only_candidate_gets_zero_semantic_and_still_ranks():
    ml = MemoryLayer.__new__(MemoryLayer)
    out = ml._hybrid_score([], [_msg("fresh", days=0, imp=0.5)], [])
    assert out[0]["semantic_score"] == 0 and out[0]["hybrid_score"] == pytest.approx(0.3 * math.exp(0) + 0.2 * 0.5)


def test_relevant_old_fact_still_beats_unrelated_recent_chatter():
    ml = MemoryLayer.__new__(MemoryLayer)
    old_relevant = _msg("old", days=60, sim=0.8, imp=0.5)          # 0.5*0.8 + 0.2*0.5 = 0.50
    recent_noise = _msg("noise", days=1, imp=0.5)                   # 0.3*exp(-0.1) + 0.1 ~= 0.37
    out = ml._hybrid_score([old_relevant], [recent_noise], [])
    assert _ids(out)[0] == "old"


def test_borderline_old_fact_loses_to_recent_chatter():
    """A relevant fact barely over the 0.7 similarity gate, with low importance, loses to unrelated recent messages."""
    ml = MemoryLayer.__new__(MemoryLayer)
    borderline = _msg("old", days=60, sim=0.71, imp=0.3)            # 0.355 + 0.06 = 0.415
    noise = [_msg(f"n{i}", days=0, imp=0.7) for i in range(3)]      # 0.3 + 0.14 = 0.44
    out = ml._hybrid_score([borderline], noise, [])
    assert _ids(out)[-1] == "old"


def test_recent_relevant_message_outside_newest_15_gets_no_recency():
    """Temporal list is the 15 newest in the last 7 days. A relevant 2-day-old message that is not among them is semantic-only."""
    ml = MemoryLayer.__new__(MemoryLayer)
    newest = [_msg(f"t{i}", days=0, imp=0.5) for i in range(15)]
    relevant = _msg("rel", days=2, sim=0.8, imp=0.5)
    out = ml._hybrid_score([relevant], newest, [])
    rel = next(m for m in out if m["id"] == "rel")
    assert rel["recency_score"] == 0


def test_important_only_candidate_scores_importance_only():
    ml = MemoryLayer.__new__(MemoryLayer)
    out = ml._hybrid_score([], [], [_msg("core", days=90, imp=0.9)])
    assert out[0]["hybrid_score"] == pytest.approx(0.2 * 0.9)


def test_transient_messages_cannot_crowd_out_all_persisted_memories(monkeypatch):
    """Regression for the old behavior where 5+ transient messages filled every slot (limit=5).
    Now the most recent transient messages keep their place and 2 slots are reserved for persisted memories."""
    transient = [_msg(f"hi{i}", text="ok") for i in range(10)]
    persisted = [_msg("fact", days=30, sim=0.9, imp=0.9), _msg("fact2", days=20, sim=0.85, imp=0.9)]
    ml = _layer(monkeypatch, transient=transient, semantic=persisted, important=persisted)
    out = asyncio.run(ml.retrieve_context("u", "what's my dog's name", limit=5, strategy="hybrid"))
    assert len(out) == 5
    assert _ids(out)[:3] == ["hi7", "hi8", "hi9"]          # newest transient, original order
    assert set(_ids(out)[3:]) == {"fact", "fact2"}


def test_transient_keeps_all_slots_when_no_persisted_candidates(monkeypatch):
    transient = [_msg(f"hi{i}", text="ok") for i in range(8)]
    ml = _layer(monkeypatch, transient=transient)
    out = asyncio.run(ml.retrieve_context("u", "q", limit=5))
    assert _ids(out) == ["hi3", "hi4", "hi5", "hi6", "hi7"]


def test_one_persisted_candidate_reserves_one_slot(monkeypatch):
    transient = [_msg(f"hi{i}", text="ok") for i in range(8)]
    ml = _layer(monkeypatch, transient=transient, semantic=[_msg("f", days=3, sim=0.9)])
    out = asyncio.run(ml.retrieve_context("u", "q", limit=5))
    assert len(out) == 5 and _ids(out)[-1] == "f"


def test_few_transient_unchanged(monkeypatch):
    ml = _layer(monkeypatch, transient=[_msg("a"), _msg("b")], semantic=[_msg("f", sim=0.9, days=2)])
    assert _ids(asyncio.run(ml.retrieve_context("u", "q", limit=5))) == ["a", "b", "f"]


def test_transient_dedup_and_order(monkeypatch):
    t = [_msg("a"), _msg("b")]
    ml = _layer(monkeypatch, transient=t, semantic=[_msg("a", sim=0.9), _msg("c", days=9, sim=0.9)])
    out = asyncio.run(ml.retrieve_context("u", "q", limit=5))
    assert _ids(out)[:2] == ["a", "b"] and _ids(out).count("a") == 1 and "c" in _ids(out)


def test_non_hybrid_strategies_return_raw_candidates(monkeypatch):
    sem = [_msg("s", sim=0.9)]
    ml = _layer(monkeypatch, semantic=sem, temporal=[_msg("t")], important=[_msg("i", imp=0.9)])
    assert _ids(asyncio.run(ml.retrieve_context("u", "q", strategy="semantic"))) == ["s"]
    assert _ids(asyncio.run(ml.retrieve_context("u", "q", strategy="temporal"))) == ["t"]
    assert _ids(asyncio.run(ml.retrieve_context("u", "q", strategy="importance"))) == ["i"]
