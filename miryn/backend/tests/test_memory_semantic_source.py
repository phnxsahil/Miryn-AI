"""Tests for embedding-source hygiene in semantic recall and query-relevant fact selection.

Offline and deterministic: embedders, sessions and fact lists are fakes, so these test the
MECHANICS (hash-fallback vectors never rank memories; relevant facts rank first). They say
nothing about real Gemini embedding quality.
"""
import asyncio
import logging

from app.services.fact_store import FactStore
from app.services.memory_layer import MemoryLayer


class _Cache:
    def get(self, k): return None
    def setex(self, *a, **k): pass
    def sadd(self, *a, **k): pass
    def expire(self, *a, **k): pass


class _HashEmbedder:
    def embed(self, text): return [0.0]
    def embed_with_source(self, text): return ([0.0], "hash_fallback")


class _GeminiEmbedder:
    def embed(self, text): return [0.0]
    def embed_with_source(self, text): return ([0.0], "gemini")


def _layer(monkeypatch, embedder):
    ml = MemoryLayer.__new__(MemoryLayer)
    ml.cache, ml.embedder, ml.logger, ml.episodic_days = _Cache(), embedder, logging.getLogger("t"), 7
    monkeypatch.setattr(ml, "_transient_search", lambda u, c, limit: [])
    monkeypatch.setattr(ml, "_temporal_search", lambda u, days, limit, sql_session=None: [{"id": "temp", "content": "t", "created_at": None, "importance_score": 0.5}])
    monkeypatch.setattr(ml, "_importance_search", lambda u, threshold, limit, sql_session=None: [])
    return ml


def test_hash_fallback_query_skips_semantic_search(monkeypatch):
    """When the query embedding is a hash pseudo-vector, semantic recall must be skipped:
    comparing it against stored vectors ranks memories by hash noise, not meaning."""
    ml = _layer(monkeypatch, _HashEmbedder())

    def forbidden(*a, **k):
        raise AssertionError("semantic search must not run on a hash-fallback query embedding")

    monkeypatch.setattr(ml, "_semantic_search", forbidden)
    out = asyncio.run(ml.retrieve_context("u", "what did I say about my dog?", limit=5))
    assert [m["id"] for m in out] == ["temp"]


def test_gemini_query_runs_semantic_search(monkeypatch):
    ml = _layer(monkeypatch, _GeminiEmbedder())
    monkeypatch.setattr(ml, "_semantic_search", lambda u, e, limit, sql_session=None: [{"id": "sem", "content": "s", "created_at": None, "importance_score": 0.5, "similarity": 0.9}])
    out = asyncio.run(ml.retrieve_context("u", "q", limit=5, strategy="semantic"))
    assert [m["id"] for m in out] == ["sem"]


class _Result:
    def mappings(self): return self
    def all(self): return []


class _Session:
    def __init__(self): self.statements = []
    def execute(self, stmt, params):
        self.statements.append(str(stmt))
        return _Result()


def test_semantic_search_sql_excludes_hash_fallback_rows(monkeypatch):
    """Stored hash-fallback pseudo-vectors must never participate in cosine matching."""
    import app.services.memory_layer as memory_layer

    monkeypatch.setattr(memory_layer, "has_sql", lambda: True)
    ml = MemoryLayer.__new__(MemoryLayer)
    session = _Session()
    ml._semantic_search("u", [0.0], limit=15, sql_session=session)
    assert len(session.statements) == 1
    assert "embedding_source <> 'hash_fallback'" in session.statements[0]


def _fact(i, content, imp):
    return {"id": i, "content": content, "memory_tier": "episodic", "importance_score": imp, "created_at": "x"}


def test_list_top_without_query_keeps_importance_order(monkeypatch):
    facts = [_fact("1", "User's dog is allergic to chicken", 0.90), _fact("2", "User likes trekking", 0.95)]
    monkeypatch.setattr(FactStore, "_list", lambda self, u, limit, minimum=None: facts[:limit])
    out = FactStore().list_top("u", 2)
    assert [f["id"] for f in out] == ["1", "2"]   # _list order untouched


def test_list_top_with_query_ranks_relevant_fact_first(monkeypatch):
    facts = [_fact("1", "User's dog is allergic to chicken", 0.90), _fact("2", "User likes trekking", 0.95)]
    monkeypatch.setattr(FactStore, "_list", lambda self, u, limit, minimum=None: facts[:limit])
    out = FactStore().list_top("u", 2, query="what food should I buy for my dog")
    assert out[0]["id"] == "1"   # relevant fact beats the more important but unrelated one


def test_list_top_with_query_fetches_wider_candidate_set(monkeypatch):
    monkeypatch.setattr(FactStore, "_list", lambda self, u, limit, minimum=None: [])
    seen = {}
    def recording(self, u, limit, minimum=None):
        seen["limit"] = limit
        return []
    monkeypatch.setattr(FactStore, "_list", recording)
    FactStore().list_top("u", 8, query="anything")
    assert seen["limit"] == 24


def test_high_importance_fact_beats_weakly_relevant_one(monkeypatch):
    """Lexical relevance must not crowd out a much more important fact."""
    facts = [
        _fact("1", "User is severely allergic to peanuts", 0.97),
        _fact("2", "User mentioned chicken biryani once", 0.40),
    ]
    monkeypatch.setattr(FactStore, "_list", lambda self, u, limit, minimum=None: facts[:limit])
    out = FactStore().list_top("u", 2, query="is chicken okay for dinner")
    # relevance: fact2 ~0.5 (chicken), fact1 0 -> scores 0.97 vs 0.90
    assert out[0]["id"] == "1"


def test_hinglish_query_ranks_matching_fact_first(monkeypatch):
    """Hinglish function words dilute but a matching content word still ranks the fact."""
    facts = [
        _fact("1", "User's dog is allergic to chicken", 0.90),
        _fact("2", "User likes trekking", 0.95),
    ]
    monkeypatch.setattr(FactStore, "_list", lambda self, u, limit, minimum=None: facts[:limit])
    out = FactStore().list_top("u", 2, query="mere dog ko kya khilau")
    assert out[0]["id"] == "1"


def test_negated_query_still_ranks_by_overlap(monkeypatch):
    """Negation is not modeled: a negated mention still surfaces the related fact
    (the correction path, not ranking, handles the change). Pins current behavior."""
    facts = [_fact("1", "User's dog is allergic to chicken", 0.90), _fact("2", "User likes trekking", 0.95)]
    monkeypatch.setattr(FactStore, "_list", lambda self, u, limit, minimum=None: facts[:limit])
    out = FactStore().list_top("u", 2, query="my dog is not allergic to chicken anymore")
    assert out[0]["id"] == "1"


def test_list_top_with_unmatched_query_falls_back_to_importance_order(monkeypatch):
    facts = [_fact("1", "a", 0.95), _fact("2", "b", 0.90)]   # importance order, as _list returns
    monkeypatch.setattr(FactStore, "_list", lambda self, u, limit, minimum=None: facts[:limit])
    out = FactStore().list_top("u", 2, query="zzzzz qqqqq")
    assert [f["id"] for f in out] == ["1", "2"]
