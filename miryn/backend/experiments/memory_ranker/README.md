# Memory ranker experiment (offline, synthetic, not wired into the app)

Question: does a learned reranker beat the hand-weighted hybrid in `memory_layer._hybrid_score` (0.5 semantic + 0.3 recency + 0.2 importance)?

- `generate_data.py`: Claude Haiku invents fictional personas (24 memories, 8 queries with relevant ids each). No real user data.
- `evaluate.py`: bge-small-en-v1.5 (local, free) cosine as semantic score; baseline vs semantic-only vs logistic regression vs GBDT; 5-fold persona-grouped CV (no persona in both train and test); persona-level bootstrap CIs. See `RESULTS.md`.

## Caveats (read before trusting any number)
- Labels are model-generated, not human or real-usage labels.
- Semantic score is bge, not Gemini. bge cosines are compressed, so the 0.3 recency term dominates the baseline. The baseline's big deficit is probably partly this scale mismatch and would differ with Gemini scores. Not tested.
- Candidate pool is all 24 memories (no candidate-stage recall loss). Importance is fixed at the repo default 0.5 for all memories; learned models get category one-hot instead of the real heuristic.
- 35 personas / 280 queries. Small.
- Baseline wins on "recent" queries, so recency matters for some intents; a learned model without query-intent signal loses there.

## Audit notes
- Generator model: claude-haiku-5-5 (cheaper tier; the user asked for Sonnet for Miryn conversation, this experiment data generation was a separate, cheaper choice and must be reported as such).
- Cost accounting: personas.cost logs token-usage-based cost only for calls whose JSON parsed. Failed (truncated JSON) calls were not logged per call, and one earlier 20-persona run was killed before saving. Logged figures are estimates from reported usage x list price, not provider-billed amounts. Conservative bound: treat total experiment spend as up to $1.00 until checked in the Anthropic console.
- Label construction: the generator wrote memories and labelled relevance itself. Paraphrase queries share fewer words with their targets (mean token overlap 0.14) than direct queries (0.40), so the kind labels hold roughly, but labels are unverified. No human review.
- Splits and tuning: GroupKFold by persona; no hyperparameters were tuned (fixed a priori: logreg defaults, HistGradientBoosting depth 3, lr 0.05, 100 iters), so no selection on test folds.
- Features such as "rank of this memory's similarity within the query" are computed per query from candidate similarities only, so they are available at serving time.
- Embedder: BAAI/bge-small-en-v1.5 via fastembed (ONNX, 384-d, local). It is NOT the app's Gemini embedder.
- Deployment constraints (not tested): any serving of this would add onnxruntime if bge were used; the rankers themselves are tiny. Nothing here is wired into the app.
- Conclusion: on this synthetic setup, semantic-only matches the learned rankers; no ML benefit demonstrated. The baseline comparison is invalid for the live system (different embedder, importance fixed, whole-memory pool).
