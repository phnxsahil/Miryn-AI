"""Property-style tests for _enforce_correction_order's comparator behavior.

No database: builds synthetic rows whose texts make the real
select_supersede_candidate validation succeed, randomizes importance order
and constraint targets, and checks the safety properties retrieval relies
on - no fact is ever dropped or duplicated, and every validated correction
ends up ahead of the fact it corrects.
"""

import random
from datetime import datetime, timedelta

from app.services.fact_store import _enforce_correction_order


def _row(i, created, marker=None, importance=0.5):
    return {
        "id": f"fact-{i}",
        "content": f"topic{i:02d} value{i:02d}",
        "category": "goal",
        "extractor": "llm",
        "created_at": created,
        "importance_score": importance,
        "corrects": marker,
    }


def _marker_for(target_i):
    return {
        "entity": f"topic{target_i:02d}",
        "attribute": "value",
        "old_value": f"value{target_i:02d}",
        "new_value": "updated",
        "polarity_old": "neutral",
        "polarity_new": "neutral",
    }


def test_randomized_dag_constraints_all_satisfied_and_complete():
    rng = random.Random(20261103)
    for _ in range(200):
        n = rng.randint(2, 12)
        base = datetime(2026, 1, 1)
        rows = []
        for i in range(n):
            created = base + timedelta(hours=i)
            marker = None
            # newer facts may correct exactly one older fact (a DAG by age)
            if i > 0 and rng.random() < 0.5:
                marker = _marker_for(rng.randint(0, i - 1))
            rows.append(_row(i, created, marker, rng.random()))
        rng.shuffle(rows)

        out = _enforce_correction_order(rows)

        assert sorted(r["id"] for r in out) == sorted(r["id"] for r in rows)
        positions = {r["id"]: k for k, r in enumerate(out)}
        for r in rows:
            marker = r["corrects"]
            if not marker:
                continue
            target = "fact-" + str(int(marker["entity"].replace("topic", "")))
            assert positions[r["id"]] < positions[target]


def test_no_markers_is_identity():
    base = datetime(2026, 1, 1)
    rows = [_row(i, base + timedelta(hours=i)) for i in range(6)]
    assert [r["id"] for r in _enforce_correction_order(rows)] == [r["id"] for r in rows]
