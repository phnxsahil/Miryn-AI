personas=35 queries=280 memories/persona=24 (candidate pool = all memories; recall ceiling 1.0)

## Overall (5-fold persona-grouped CV; mean [95% persona-bootstrap CI])

| ranker | nDCG@5 | recall@5 | MRR |
|---|---|---|---|
| semantic_only | 0.826 [0.799,0.853] | 0.899 [0.872,0.924] | 0.857 [0.830,0.884] |
| baseline_0.5/0.3/0.2 | 0.430 [0.386,0.474] | 0.617 [0.555,0.675] | 0.455 [0.406,0.506] |
| logreg | 0.844 [0.816,0.869] | 0.908 [0.880,0.935] | 0.878 [0.853,0.902] |
| gbdt | 0.839 [0.812,0.866] | 0.914 [0.893,0.937] | 0.862 [0.834,0.888] |

## Paired difference vs baseline (positive = learned better)

| ranker | dnDCG@5 | drecall@5 | dMRR |
|---|---|---|---|
| semantic_only | +0.397 [+0.352,+0.438] | +0.282 [+0.221,+0.339] | +0.403 [+0.354,+0.450] |
| logreg | +0.414 [+0.372,+0.457] | +0.292 [+0.236,+0.344] | +0.424 [+0.376,+0.471] |
| gbdt | +0.409 [+0.367,+0.454] | +0.298 [+0.243,+0.353] | +0.407 [+0.358,+0.455] |

## Learned vs semantic-only (the honest comparison)

| ranker | dnDCG@5 | drecall@5 | dMRR |
|---|---|---|---|
| logreg | +0.018 [+0.005,+0.030] | +0.010 [-0.004,+0.024] | +0.021 [+0.004,+0.039] |
| gbdt | +0.013 [-0.001,+0.026] | +0.015 [-0.006,+0.036] | +0.004 [-0.006,+0.014] |

## nDCG@5 by query kind (baseline / logreg / gbdt)

| kind | n | baseline | logreg | gbdt |
|---|---|---|---|---|
| advice | 70 | 0.412 | 0.783 | 0.756 |
| correction | 35 | 0.296 | 0.839 | 0.784 |
| direct | 70 | 0.459 | 0.996 | 0.984 |
| paraphrase | 70 | 0.280 | 0.829 | 0.841 |
| recent | 35 | 0.838 | 0.696 | 0.766 |
