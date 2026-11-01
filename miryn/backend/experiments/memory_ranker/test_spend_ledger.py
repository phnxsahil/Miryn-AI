"""Offline tests for the spend ledger and the generator's call path. No network, no paid calls."""
import asyncio, json, tempfile, threading, unittest, types
from pathlib import Path
import spend_ledger as sl
import generate_data as gd

def mk(cap=1.0, run_cap=None, d=None):
    d = d or tempfile.mkdtemp()
    return sl.Ledger(Path(d) / "l.sqlite", cap, run_id="r1", run_cap_usd=run_cap), d

class LedgerTests(unittest.TestCase):
    def test_total_cap_refuses_before_call(self):
        L, _ = mk(cap=0.10)
        L.reserve(0.06, "m")
        with self.assertRaises(sl.BudgetExceeded):
            L.reserve(0.06, "m")

    def test_prior_unknown_spend_is_deducted(self):
        L, _ = mk(cap=0.50)
        L.add_prior(0.45, "killed run, worst case")
        with self.assertRaises(sl.BudgetExceeded):
            L.reserve(0.10, "m")

    def test_run_cap(self):
        L, _ = mk(cap=10, run_cap=0.05)
        L.reserve(0.04, "m")
        with self.assertRaises(sl.BudgetExceeded):
            L.reserve(0.02, "m")

    def test_failure_stays_counted_at_worst_case(self):
        L, _ = mk()
        cid = L.reserve(0.2, "m"); L.mark_ambiguous(cid, "timeout")
        self.assertAlmostEqual(L.total_counted(), 0.2)

    def test_restart_keeps_interrupted_reservation(self):
        L, d = mk()
        L.reserve(0.3, "m")           # process "killed" here: never settled
        L2, _ = mk(d=d)               # restart on same file
        self.assertAlmostEqual(L2.total_counted(), 0.3)

    def test_settle_lowers_to_actual_and_reconcile_overrides(self):
        L, _ = mk()
        cid = L.reserve(0.2, "m"); L.settle(cid, 0.01, 100, 200)
        self.assertAlmostEqual(L.total_counted(), 0.01)
        L.reconcile(cid, 0.02)
        self.assertAlmostEqual(L.total_counted(), 0.02)

    def test_concurrent_reservations_never_exceed_cap(self):
        L, d = mk(cap=1.0)
        ok = []
        def w():
            lg = sl.Ledger(Path(d) / "l.sqlite", 1.0, run_id="r1")
            for _ in range(20):
                try:
                    lg.reserve(0.05, "m"); ok.append(1)
                except sl.BudgetExceeded:
                    pass
        ts = [threading.Thread(target=w) for _ in range(8)]
        [t.start() for t in ts]; [t.join() for t in ts]
        self.assertLessEqual(L.total_counted(), 1.0 + 1e-9)
        self.assertIn(len(ok), (19, 20))  # 1.0/0.05; float rounding may refuse the last one

def fake_client(behavior):
    async def create(**kw):
        return behavior()
    return types.SimpleNamespace(messages=types.SimpleNamespace(create=create))

def resp(text, i=1000, o=2000):
    return types.SimpleNamespace(usage=types.SimpleNamespace(input_tokens=i, output_tokens=o),
                                 content=[types.SimpleNamespace(type="text", text=text)])

class GeneratorPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); gd.OUT = self.tmp / "p.jsonl"
        self.L, _ = mk(cap=5.0, d=self.tmp)
    def run1(self, behavior):
        return asyncio.run(gd.one(fake_client(behavior), "seed", 0, self.L))

    def test_success_settles_and_writes(self):
        r = self.run1(lambda: resp(json.dumps({"persona": "x", "memories": [], "queries": []})))
        self.assertIsNotNone(r)
        self.assertEqual(self.L.summary()["settled"]["n"], 1)
        self.assertTrue(gd.OUT.exists())

    def test_exception_counts_worst_case(self):
        def boom(): raise ConnectionError("net down")
        self.assertIsNone(self.run1(boom))
        s = self.L.summary()
        self.assertEqual(s["ambiguous"]["n"], 1)
        self.assertGreater(s["ambiguous"]["usd"], 0.017)  # about max_tokens * output price

    def test_unparseable_response_is_still_billed(self):
        self.assertIsNone(self.run1(lambda: resp("{truncated", 4000, 7000)))
        s = self.L.summary()
        self.assertEqual(s["settled"]["n"], 1)
        self.assertAlmostEqual(s["settled"]["usd"], (4000 * 0.5 + 7000 * 2.5) / 1e6)
        self.assertFalse(gd.OUT.exists())

    def test_budget_exceeded_raises_before_any_call(self):
        L, _ = mk(cap=0.001, d=self.tmp / "x" if False else None)
        called = []
        def b(): called.append(1); return resp("{}")
        with self.assertRaises(sl.BudgetExceeded):
            asyncio.run(gd.one(fake_client(b), "seed", 0, L))
        self.assertEqual(called, [])

    def test_main_refuses_without_approval_env(self):
        import os
        os.environ.pop("EXPERIMENT_PAID_RUN_APPROVED", None)
        with self.assertRaises(SystemExit):
            asyncio.run(gd.main(1))

if __name__ == "__main__":
    unittest.main()
