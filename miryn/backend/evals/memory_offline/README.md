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
    python3 evals/memory_offline/offline_extract.py > offline_report.json

Baseline on `main` at the time of the PR-35 review round: 17/39 checks pass.
With the review branch: 22/39 (see the PR body for the fail→PASS diff).

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
