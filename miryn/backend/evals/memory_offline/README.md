# memory_offline — synthetic offline memory-extraction eval pack

## What this is

A reproducible offline check of Miryn's heuristic memory extractor
(`app/services/importance.py::score_message_heuristic`) against a fixed pack of
synthetic conversations. No network, no database, no LLM calls, no secrets.

## Contents

- `scenarios.jsonl` — 36 synthetic multi-session conversations (61 user turns)
  with per-scenario `expect.store` / `expect.not_store` checks (39 checks).
- `offline_extract.py` — runner. Imports the repo's verbatim extractor and
  prints a JSON report with per-check pass/fail and category totals.

## Run

    cd miryn/backend
    python3 evals/memory_offline/offline_extract.py                       # dev pack -> offline_report.json
    python3 evals/memory_offline/offline_extract.py SCENARIOS_JSONL REPORT_JSON   # explicit paths

Files: `scenarios.jsonl` is the dev pack the heuristic patterns were tuned
against; `scenarios_holdout.jsonl` is a small VALIDATION set - written after
tuning, but touched during fixing (one expectation reclassified, four
scenarios added to pin fixes), so it is NOT an unseen holdout and its score
must not be read as generalization evidence; `offline_report_main.json` /
`offline_report_branch.json` / `offline_report_holdout.json` are the
committed reports.

Scores: baseline `main` 17/39; review branch at PR-35 review head 22/39;
current branch 39/39 dev + 16/16 validation. Both packs informed the
patterns, so both scores are upper bounds. Audit trail: HO-08's original
not_store expectation was reclassified to store (preserved in its `audit`
field) after the dev pack's QT-02 showed third-party relationship facts are
stored on purpose; HO-13/14/15/16 were added to pin the probe-detection
fixes they verify. The holdout includes adversarial guards for the
broadest new patterns (Hinglish "kya" questions, aux+my inversions like
"Is my interview today?", third-party Hindi without first-person markers,
third-party "her bday"). Two design notes: (1) third-party relationship
facts are stored on purpose - the dev pack's QT-02 expects "My brother
Arjun loves trekking" to be stored with speaker normalization - so HO-08
checks storage, and recall-time attribution stays untested in offline
mode; (2) probe detection now also treats "kya" as a question lead and
aux+my ("is my interview today?") as inversion, so those questions are
not stored as facts.

## Provenance and rights

- Every conversation in `scenarios.jsonl` is **synthetic**: personas, names,
  dates and events were invented for this evaluation. No message from any real
  user or private chat is included, quoted, or paraphrased.
- Scenario categories are inspired by the public LongMemEval benchmark
  (arXiv:2410.10813) — single-session-user, multi-session, temporal-reasoning,
  knowledge-update and abstention/recall-probe styles — re-authored here as
  original synthetic text. No LongMemEval data rows are redistributed.
- The pack and runner were authored for the Miryn-AI project as part of the
  PR-35 review work and are contributed to this repository under the
  repository's own license. They may be kept, run, and extended in-repo.
- Known limits: this pack measures heuristic storage behavior only. It does
  not exercise supersession linking, recall quality, assistant replies, or any
  LLM path, and a pass here is not evidence of end-to-end correctness.
