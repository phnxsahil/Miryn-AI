"""Answer-level memory-behaviour replay (offline-first, fictional scenarios).

For each fictional scenario this builds the REAL system prompt and user context
(LLMService._build_system_prompt + _format_context) from seeded memories and a
probe, then checks:

- prompt_must_include: deterministic checks that the context/prompt carry what
  the behaviour rule needs (always run, offline).
- reply_must_include / reply_must_not_include: checked against a GENERATED
  reply only when --with-model runs with a real provider (GATED: requires the
  spend/billing grounding to be established first; not run by default).

BOUNDARY: prompt-level checks prove the instructions and context are present,
NOT that answers follow them. Answer-level validation needs real model runs.

Run from miryn/backend:  python3 evals/answer_replay/run_answer_replay.py
"""
import asyncio
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from app.services.llm_service import LLMService  # noqa: E402


def build_prompt(svc, scenario):
    identity = dict(scenario.get("identity") or {})
    identity.setdefault("preset", "companion")
    system = svc._build_system_prompt(identity)
    known_facts = [f.get("content", "") for f in scenario.get("facts") or []]
    context = svc._format_context({"known_facts": known_facts, "memories": scenario.get("memories") or []})
    return system, context


def main():
    with_model = "--with-model" in sys.argv
    scenarios = json.loads((BACKEND / "evals/answer_replay/scenarios.json").read_text())["scenarios"]
    svc = LLMService()
    failures = 0
    for scenario in scenarios:
        system, context = build_prompt(svc, scenario)
        combined = system + "\n" + context
        missing = [s for s in scenario.get("prompt_must_include", []) if s not in combined]
        status = "PASS" if not missing else "FAIL"
        failures += 0 if not missing else 1
        print(f"{status}  {scenario['name']} (prompt-level)")
        for s in missing:
            print(f"  missing in prompt: {s!r}")
        if with_model:
            print("  --with-model: gated on spend grounding; not implemented for unattended runs")
            failures += 1
    print(f"\n{len(scenarios) - failures}/{len(scenarios)} scenario prompt checks pass "
          "(prompt-level only; answer-level needs gated real model runs)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
