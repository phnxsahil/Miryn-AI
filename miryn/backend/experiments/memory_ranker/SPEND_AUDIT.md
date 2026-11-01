# Spend audit: conversation eval, Nov 2

Fictional data only. Numbers are token x list-price estimates, not provider-billed. Real spend is unverified until the Anthropic console is read.

## What happened
Three invocations of conv_eval.py (6 cases each, run cap $0.50) counted $0.2655 + $0.1458 + $0.1338 = $0.545 in total.

| Attempt | Outcome | Counted |
|---|---|---|
| 1 | Failed locally before any request (an import stub had replaced the SDK with a mock). Counted at worst case, so an over-count. | $0.2655 |
| 2 | 18 real calls, the judge output was unusable for all 6 cases. | $0.1338 |
| 3 | 18 more real calls, judge usable for 3 of 6. | $0.1458 |

## Root cause
The run cap was keyed by a random per-process run id. Each invocation started with a fresh id, so the $0.50 cap reset each time. Every run stayed under $0.50 on its own, and the $50 total cap and the $5 prior hold were never at risk. The cumulative figure still passed the $0.50 the owner agreed for this batch. It was a guard design bug, not an unknown-settlement bug.

## Fix
- Paid runs now require `--campaign <stable id>`. The run cap counts every invocation with that id.
- Completed reply pairs are saved to data/replies.jsonl and reused instead of repaid.
- The judge parser strips code fences and rejects truncated output (stop reason max_tokens), incomplete JSON and out-of-range values.
- Tests: 12 offline tests (see test_conv_eval.py), including a three-process campaign cap test and deterministic judge-format fixtures.
- Attempts 2 and 3 replies were not saved, so they cannot be reused.

## Limits of any result
Uncalibrated model judge, oracle context (gold memories given), tiny n. Not retrieval or end-to-end, no quality claim.
