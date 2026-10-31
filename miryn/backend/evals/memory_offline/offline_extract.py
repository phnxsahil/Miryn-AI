#!/usr/bin/env python3
"""Offline eval: run Miryn's real heuristic extractor (verbatim repo code, no network,
no DB, no LLM) over the scenario pack's user turns and score storage expectations.

Scope: heuristic storage behavior only. Supersession, recall and assistant-reply
checks are out of scope for this mode (they need the full stack)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # miryn/backend
from app.services.importance import score_message_heuristic  # verbatim repo code

def fact_has_all(text, toks):
    low = text.lower()
    return all(t.lower() in low for t in toks)

# Optional argv: scenarios path (default: the dev pack next to this script) and
# report output path (default: offline_report.json in cwd).
_scen_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "scenarios.jsonl"
_report_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("offline_report.json")
scenarios = [json.loads(l) for l in open(_scen_path) if l.strip()]
report = {"mode": "miryn-heuristic-offline", "code_source": "repo main, app/services/importance.py score_message_heuristic", "scenarios": []}
tot_p = tot_t = 0
by_cat = {}
for sc in scenarios:
    extracted = []
    for sess in sc["sessions"]:
        for turn in sess["turns"]:
            for f in score_message_heuristic(turn):
                extracted.append({"turn": turn, "fact": f.text, "category": f.category,
                                  "importance": round(f.importance, 3)})
    texts = [e["fact"] for e in extracted]
    checks = []
    for item in sc["expect"].get("store", []):
        ok = any(fact_has_all(t, item["all_of"]) for t in texts)
        checks.append({"check": f"store {item['all_of']}", "pass": ok})
    for item in sc["expect"].get("not_store", []):
        bad = [t for t in texts if fact_has_all(t, item["no_fact_with_all"])]
        checks.append({"check": f"not_store {item['no_fact_with_all']}", "pass": not bad,
                       "offending": bad[:2]})
    p = sum(1 for c in checks if c["pass"]); t = len(checks)
    tot_p += p; tot_t += t
    agg = by_cat.setdefault(sc["category"], [0, 0]); agg[0] += p; agg[1] += t
    report["scenarios"].append({"id": sc["id"], "category": sc["category"],
                                "checks_passed": p, "checks_total": t,
                                "extracted": extracted, "checks": checks})
report["totals"] = {"checks_passed": tot_p, "checks_total": tot_t,
                    "pass_rate": round(tot_p / tot_t, 3) if tot_t else None}
report["by_category"] = {k: {"passed": v[0], "total": v[1]} for k, v in sorted(by_cat.items())}
json.dump(report, open(_report_path, "w"), ensure_ascii=False, indent=1)

print(f"storage checks: {tot_p}/{tot_t} passed ({report['totals']['pass_rate']})")
for k, v in report["by_category"].items():
    print(f"  {k:28s} {v['passed']}/{v['total']}")
print("\nGuard-category detail (junk that would be stored):")
for s in report["scenarios"]:
    for c in s["checks"]:
        if not c["pass"] and c["check"].startswith("not_store"):
            print(f"  {s['id']}: STORED JUNK -> {c['offending']}")
print("\nMissed durable facts:")
for s in report["scenarios"]:
    for c in s["checks"]:
        if not c["pass"] and c["check"].startswith("store "):
            print(f"  {s['id']}: MISSED -> {c['check']}")
