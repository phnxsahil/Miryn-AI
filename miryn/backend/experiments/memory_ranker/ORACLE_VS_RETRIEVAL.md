# Oracle context vs retrieval (offline, free)

Why this exists: conv_eval.py gives the model the gold-relevant memories (oracle context). That says nothing about what Miryn's retrieval actually returns. This note puts the two next to each other using numbers already in RESULTS.md. No new model calls, no real user data.

## Numbers (35 fictional personas, 280 queries, 24 memories each; recall@5 = share of gold memories in the top 5)
| context source | recall@5 | note |
|---|---|---|
| Oracle (conv_eval "memory" arm) | 1.00 by construction | gold memories always included, plus 2 distractors |
| Stand-in for production hybrid (0.5 semantic + 0.3 recency + 0.2 importance) | 0.617 [0.555, 0.675] | nDCG@5 0.430 |
| Semantic similarity only | 0.899 [0.872, 0.924] | nDCG@5 0.826 |
| Learned logreg / GBDT | 0.908 / 0.914 | only +0.01 over semantic-only, CI includes 0 for recall |

## What the stand-in is and is not
- Same formula as production: `_hybrid_score` in app/services/memory_layer.py uses alpha 0.5, beta 0.3, gamma 0.2, and recency exp(-0.1 * days). Checked against main on Nov 2.
- Not the same candidate logic: production merges three lists (semantic, recent, important). A message found only by the semantic list gets recency 0, and one found only by the recent list gets semantic 0. The stand-in scores every memory on all three. Production's real candidate sizes and pgvector search are not simulated.
- Embedder is bge-small, not the Gemini embeddings production uses. Pool is 24 memories per persona, far smaller than a real history. Labels are model-made, never human-checked. Importance uses the repo's heuristic, not the live LLM extractor.

## Reading
- In this synthetic setup the hand-weighted recency term hurts: with decay 0.1 per day, a 30-day-old fact keeps about 5% of its recency score, so old relevant facts lose to recent irrelevant ones. Semantic-only beat the hybrid by +0.397 nDCG@5 (CI +0.352 to +0.438).
- This does NOT show production is that bad. It shows the weights deserve a test on a faithful simulation of the candidate merge, with the live embedder, before anyone changes them.
- Consequence for conv_eval: any "memory arm wins" result under oracle context is an upper bound on what retrieval would deliver, not a measure of Miryn.
- Not done: judge calibration. It needs paid judge outputs, and paid tests are on hold. A developer-labeled calibration set would not be an independent human label.
