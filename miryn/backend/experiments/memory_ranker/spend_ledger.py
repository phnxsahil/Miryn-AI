"""Durable pre-call spend ledger for paid experiment runs (SQLite, stdlib only).

Rules (conservative on purpose):
- reserve() writes a durable row BEFORE the API call, at the call's worst-case cost, inside an
  exclusive transaction, and refuses if the total, run, or remaining budget would be exceeded.
- settle() replaces the reservation with usage-based cost only when a response with usage arrived.
- Any other outcome (exception, timeout, kill, restart, parse failure before settle) leaves the row
  at its reserved worst case: state 'reserved' (in flight or interrupted) or 'ambiguous' (marked failed).
  Unknown billing is therefore counted, never assumed zero.
- reconcile() lets a human replace an ambiguous/reserved row with a billed figure from the provider console.
- add_prior() records spend that happened outside the ledger (e.g. earlier unlogged runs) as a deduction.
Costs are token x list-price estimates, not provider-billed amounts, until reconciled.
"""
import sqlite3, time, uuid
from contextlib import closing

class BudgetExceeded(RuntimeError):
    pass

class Ledger:
    def __init__(self, path, total_cap_usd, run_id=None, run_cap_usd=None):
        self.path, self.total_cap, self.run_cap = str(path), float(total_cap_usd), run_cap_usd
        self.run_id = run_id or uuid.uuid4().hex[:8]
        with closing(self._c()) as c:
            c.execute("""CREATE TABLE IF NOT EXISTS calls(
                id TEXT PRIMARY KEY, run_id TEXT, ts REAL, state TEXT, reserved_usd REAL,
                actual_usd REAL, model TEXT, in_tok INTEGER, out_tok INTEGER, note TEXT)""")
            c.commit()

    def _c(self):
        c = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        c.execute("PRAGMA journal_mode=WAL")
        return c

    @staticmethod
    def _counted(state, reserved, actual):
        return actual if state in ("settled", "reconciled", "prior") and actual is not None else reserved

    def _sum(self, c, run_id=None):
        q = "SELECT state, reserved_usd, actual_usd FROM calls" + (" WHERE run_id=?" if run_id else "")
        rows = c.execute(q, (run_id,) if run_id else ()).fetchall()
        return sum(self._counted(*r) for r in rows)

    def total_counted(self):
        with closing(self._c()) as c:
            return self._sum(c)

    def add_prior(self, usd, note):
        with closing(self._c()) as c:
            c.execute("INSERT INTO calls VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (uuid.uuid4().hex, "prior", time.time(), "prior", usd, usd, None, None, None, note))

    def reserve(self, worst_usd, model):
        cid = uuid.uuid4().hex
        with closing(self._c()) as c:
            c.execute("BEGIN IMMEDIATE")
            try:
                if self._sum(c) + worst_usd > self.total_cap:
                    raise BudgetExceeded("total cap")
                if self.run_cap is not None and self._sum(c, self.run_id) + worst_usd > self.run_cap:
                    raise BudgetExceeded("run cap")
                c.execute("INSERT INTO calls VALUES(?,?,?,?,?,?,?,?,?,?)",
                          (cid, self.run_id, time.time(), "reserved", worst_usd, None, model, None, None, None))
                c.execute("COMMIT")
            except BaseException:
                c.execute("ROLLBACK")
                raise
        return cid

    def settle(self, cid, actual_usd, in_tok, out_tok):
        with closing(self._c()) as c:
            c.execute("UPDATE calls SET state='settled', actual_usd=?, in_tok=?, out_tok=? WHERE id=?",
                      (actual_usd, in_tok, out_tok, cid))

    def mark_ambiguous(self, cid, note):
        with closing(self._c()) as c:
            c.execute("UPDATE calls SET state='ambiguous', note=? WHERE id=? AND state='reserved'", (note[:200], cid))

    def reconcile(self, cid, billed_usd, note="console"):
        with closing(self._c()) as c:
            c.execute("UPDATE calls SET state='reconciled', actual_usd=?, note=? WHERE id=?", (billed_usd, note, cid))

    def summary(self):
        with closing(self._c()) as c:
            rows = c.execute("SELECT state, count(*), sum(CASE WHEN actual_usd IS NOT NULL AND state IN ('settled','reconciled','prior') THEN actual_usd ELSE reserved_usd END) FROM calls GROUP BY state").fetchall()
        return {s: {"n": n, "usd": round(u or 0, 6)} for s, n, u in rows}
