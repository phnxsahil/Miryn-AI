import asyncio, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
import conv_eval as ce
from spend_ledger import Ledger, BudgetExceeded

class Usage: input_tokens, output_tokens = 100, 50
class Blk: type = "text"; text = "ok"
class Resp: usage = Usage(); content = [Blk()]
class Msgs:
    def __init__(s, behavior): s.b, s.n = behavior, 0
    async def create(s, **kw):
        s.n += 1
        if s.b == "ok": return Resp()
        raise s.b
class Client:
    def __init__(s, b): s.messages = Msgs(b)

def mk(cap=10, run_cap=None):
    d = tempfile.mkdtemp(); return Ledger(d + "/l.sqlite", cap, run_cap_usd=run_cap)

def run(coro): return asyncio.run(coro)

def test_reserve_before_call_and_settle():
    l = mk(); r = ce.Runner(l, Client("ok"), False)
    assert run(r.call("claude-sonnet-5-5", "s", "u", 100)) == "ok"
    assert l.summary()["settled"]["n"] == 1

def test_exception_stays_counted_at_worst_case():
    l = mk(); r = ce.Runner(l, Client(RuntimeError("net")), False)
    assert run(r.call("claude-sonnet-5-5", "s", "u", 400)) is None
    sm = l.summary(); assert sm["ambiguous"]["usd"] > 0 and "settled" not in sm

def test_cancel_during_call_stays_reserved():
    l = mk(); r = ce.Runner(l, Client(asyncio.CancelledError()), False)
    try: run(r.call("claude-sonnet-5-5", "s", "u", 400))
    except BaseException: pass
    assert l.total_counted() > 0   # counted at worst case, never zero

def test_budget_blocks_before_any_sdk_call():
    l = mk(cap=0.0001); c = Client("ok"); r = ce.Runner(l, c, False)
    try: run(r.call("claude-sonnet-5-5", "s", "u", 400)); assert False
    except BudgetExceeded: pass
    assert c.messages.n == 0

def test_prior_counted_once_against_total():
    l = mk(cap=1.0); l.add_prior(0.998, "prior"); c = Client("ok"); r = ce.Runner(l, c, False)
    try: run(r.call("claude-sonnet-5-5", "s", "u", 400)); assert False
    except BudgetExceeded: pass
    assert c.messages.n == 0

def test_judge_call_is_ledgered_too():
    l = mk(); r = ce.Runner(l, Client("ok"), False)
    run(r.call(ce.JUDGE_MODEL, "", "judge prompt", 300)); assert l.summary()["settled"]["n"] == 1

def test_paid_run_refused_without_approval():
    import subprocess
    env = {k: v for k, v in os.environ.items() if not k.startswith("EXPERIMENT_")}
    p = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "conv_eval.py")], capture_output=True, text=True, env=env)
    assert p.returncode != 0 and "refusing" in (p.stdout + p.stderr)

def test_model_ids_are_verified_ones():
    assert ce.REPLY_MODEL == "claude-sonnet-5-5" and ce.JUDGE_MODEL == "claude-haiku-5-5"
