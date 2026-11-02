"""Offline retrieval-ranking eval for Miryn's memory layer.

Reproduces the production retrieval pipeline mechanics without a database or
network (beyond an initial local model download): semantic candidates are core
memories with cosine similarity > 0.7, temporal candidates are episodic memories
<= 7 days old, important candidates have importance >= 0.7; the hybrid score is
the production 0.5/0.3/0.2 blend from app.services.memory_layer.

Usage: python3 evals/memory_retrieval/run_retrieval_eval.py [embedder]
embedder: bge-small (default, native 384) | bge-base-avg384 (768 averaged to
384, a proxy for the production Gemini 3072->384 averaging) | hash (production
hash fallback; expected near-random)

Synthetic data only: personas and facts are invented for this eval.
"""
import json, math, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent))
from app.services.memory_layer import MemoryLayer

HERE = Path(__file__).resolve().parent
SEM_THRESHOLD = 0.7
EPISODIC_DAYS = 7
IMP_THRESHOLD = 0.7
LIMIT = 5

def load(name):
    text = (HERE / name).read_text()
    if name.endswith(".json"):
        return json.loads(text)
    return [json.loads(l) for l in text.splitlines() if l.strip()]

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)

def embedder(name):
    if name == "hash":
        from app.core.embeddings import EmbeddingService
        svc = EmbeddingService(dim=384)
        return lambda texts: [svc._hash_embed(t) for t in texts]
    model_name = {"bge-small": "BAAI/bge-small-en-v1.5", "bge-base-avg384": "BAAI/bge-base-en-v1.5"}[name]
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    svc_dim = 384
    from app.core.embeddings import EmbeddingService
    comp = EmbeddingService(dim=svc_dim)._compress
    def _embed(texts):
        vecs = model.encode(texts, normalize_embeddings=True).tolist()
        return [comp(v) for v in vecs]
    return _embed

def run(name):
    memories = load("scenarios.json")["memories"]
    queries = load("queries.jsonl")
    embed = embedder(name)
    mem_vecs = dict(zip([m["id"] for m in memories], embed([m["content"] for m in memories])))
    q_vecs = embed([q["query"] for q in queries])
    ml = MemoryLayer.__new__(MemoryLayer)
    rows = []
    for q, qv in zip(queries, q_vecs):
        semantic, temporal, important = [], [], []
        for m, mv in zip(memories, mem_vecs.values()):
            sim = cosine(qv, mv)
            if m["tier"] == "core" and sim > SEM_THRESHOLD:
                semantic.append({**m, "similarity": sim, "created_at": None})
            if m["days_old"] <= EPISODIC_DAYS:
                temporal.append({**m, "created_at": _iso_days_ago(m["days_old"]), "importance_score": m["importance"]})
            if m["importance"] >= IMP_THRESHOLD:
                important.append({**m, "created_at": None, "importance_score": m["importance"]})
        for lst in (semantic,):
            for r in lst:
                r["importance_score"] = r["importance"]
        semantic.sort(key=lambda r: r["similarity"], reverse=True)
        temporal.sort(key=lambda r: r["days_old"])
        important.sort(key=lambda r: r["importance_score"], reverse=True)
        semantic, temporal, important = semantic[:15], temporal[:15], important[:15]
        scored = ml._hybrid_score(semantic, temporal, important)
        top = [r["id"] for r in scored[:LIMIT]]
        rel = set(q["relevant"]); intr = set(q["intrusive"])
        hit = len(rel & set(top)); rr = 0.0
        for rank, mid in enumerate(top, 1):
            if mid in rel:
                rr = 1.0 / rank; break
        intrusion = int(bool(intr & set(top)))
        rows.append({"id": q["id"], "query": q["query"], "top5": top, "recall_hit": hit,
                     "relevant": len(rel), "rr": rr, "intrusion": intrusion, "note": q["note"]})
    n = len(rows)
    rel_total = sum(r["relevant"] for r in rows)
    print(f"=== embedder: {name} ===")
    for r in rows:
        print(f"{r['id']}: top5={r['top5']} hit={r['recall_hit']}/{r['relevant']} rr={r['rr']:.2f} intrusion={r['intrusion']}  # {r['note']}")
    print(f"RECALL@5: {sum(r['recall_hit'] for r in rows)}/{rel_total}  MRR: {sum(r['rr'] for r in rows)/max(n,1):.3f}  INTRUSIONS: {sum(r['intrusion'] for r in rows)}")

from datetime import datetime, timedelta
def _iso_days_ago(d):
    return (datetime.utcnow() - timedelta(days=d, hours=1)).isoformat()

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "bge-small")
