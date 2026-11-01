personas=35 queries=280 memories/persona=24 (candidate pool = all memories; recall ceiling 1.0)

## Overall (5-fold persona-grouped CV; mean [95% persona-bootstrap CI])

| ranker | nDCG@5 | recall@5 | MRR |
|---|---|---|---|
| semantic_only | 0.826 [0.799,0.853] | 0.899 [0.872,0.924] | 0.857 [0.830,0.884] |
| baseline_0.5/0.3/0.2 | 0.426 [0.384,0.468] | 0.619 [0.558,0.682] | 0.451 [0.409,0.496] |
| logreg | 0.839 [0.812,0.864] | 0.907 [0.881,0.930] | 0.871 [0.846,0.895] |
| gbdt | 0.839 [0.811,0.867] | 0.912 [0.886,0.938] | 0.863 [0.834,0.889] |

## Paired difference vs baseline (positive = learned better)

| ranker | dnDCG@5 | drecall@5 | dMRR |
|---|---|---|---|
| semantic_only | +0.400 [+0.358,+0.441] | +0.280 [+0.213,+0.343] | +0.406 [+0.361,+0.448] |
| logreg | +0.413 [+0.371,+0.455] | +0.287 [+0.229,+0.345] | +0.420 [+0.376,+0.463] |
| gbdt | +0.414 [+0.373,+0.454] | +0.293 [+0.236,+0.352] | +0.411 [+0.367,+0.455] |

## Learned vs semantic-only (the honest comparison)

| ranker | dnDCG@5 | drecall@5 | dMRR |
|---|---|---|---|
| logreg | +0.013 [+0.001,+0.025] | +0.008 [-0.004,+0.021] | +0.014 [-0.005,+0.032] |
| gbdt | +0.013 [-0.001,+0.027] | +0.014 [-0.010,+0.036] | +0.005 [-0.006,+0.016] |

## nDCG@5 by query kind (baseline / logreg / gbdt)

| kind | n | baseline | logreg | gbdt |
|---|---|---|---|---|
| advice | 70 | 0.414 | 0.779 | 0.753 |
| correction | 35 | 0.275 | 0.843 | 0.788 |
| direct | 70 | 0.451 | 0.996 | 0.984 |
| paraphrase | 70 | 0.262 | 0.818 | 0.839 |
| recent | 35 | 0.875 | 0.682 | 0.775 |
