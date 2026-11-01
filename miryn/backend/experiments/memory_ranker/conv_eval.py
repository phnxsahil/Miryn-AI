"""Fictional conversation eval: does Miryn's REAL prompt builders + memory context beat a bare model?

Arms (same model, same persona, same query):
  bare    : Miryn system prompt, no memory context
  memory  : Miryn system prompt + _format_context(...) with the persona's gold-relevant memories + 2 distractors
This isolates the reply layer given good retrieval. It does NOT test retrieval (see evaluate.py).
Judge: blinded pairwise (random A/B order) rubric, Haiku. Judge labels are model-made, not human-verified.
All data is fictional (data/personas.jsonl). Every paid call is reserved in the spend ledger BEFORE it is made.
Refuses to run paid unless EXPERIMENT_PAID_RUN_APPROVED=yes and EXPERIMENT_TOTAL_CAP_USD are set. --mock runs offline.
"""
import argparse, asyncio, json, os, random, sys, types
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent.parent))
from spend_ledger import Ledger, BudgetExceeded

def load_prompt_builders():
    """Import the real LLMService prompt methods; stub heavy third-party SDKs that are not needed to build prompts."""
    from unittest.mock import MagicMock
    for _ in range(40):
        try:
            from app.services.llm_service import LLMService
            return LLMService.__new__(LLMService)
        except ModuleNotFoundError as e:
            root = (e.name or "").split(".")[0]
            if not root or root == "app": raise
            sys.modules[root] = MagicMock()
            for k in [k for k in sys.modules if k.startswith("app.")]: del sys.modules[k]
    raise RuntimeError("could not import LLMService")

REPLY_MODEL = os.environ.get("EXPERIMENT_REPLY_MODEL", "claude-sonnet-5-5")
JUDGE_MODEL = os.environ.get("EXPERIMENT_JUDGE_MODEL", "claude-haiku-5-5")
PRICE = {"sonnet": (3.0, 15.0), "haiku": (1.0, 5.0)}   # USD/MTok. CONSERVATIVE: above listed Sonnet 5.5 ($2/$10) and Haiku 5.5 rates, so reservations over-count
def price(model): return PRICE["sonnet" if "sonnet" in model else "haiku"]
def worst(model, text, max_tokens):
    pi, po = price(model); return ((len(text.encode()) + 1024) * pi + max_tokens * po) / 1e6

IDENT = {"traits": {}, "values": {}, "beliefs": [], "open_loops": [], "preset": "companion"}
JUDGE = """You compare two replies (A and B) from a companion chat app. The app's stored memories about the user are listed. 
Memories:
{mem}
User now says: {q}
Query kind: {kind}. Memories that SHOULD matter: {rel}.
Reply A:
{a}
Reply B:
{b}
Return ONLY JSON: {{"a_uses_relevant_memory": 0-2, "b_uses_relevant_memory": 0-2, "a_wrong_or_stale_fact": true|false, "b_wrong_or_stale_fact": true|false, "a_natural_tone": 0-2, "b_natural_tone": 0-2, "winner": "A"|"B"|"tie"}}
Score uses_relevant_memory 0 = ignores it, 2 = uses it naturally. wrong_or_stale_fact = states something that contradicts the listed memories (e.g. an old fact after a newer one replaced it)."""

def build_case(p, q, ident, svc, rng):
    mem = {m["id"]: m for m in p["memories"]}
    rel = [mem[i] for i in q["relevant"] if i in mem]
    others = [m for m in p["memories"] if m["id"] not in q["relevant"]]
    picks = rel + rng.sample(others, min(2, len(others)))
    rng.shuffle(picks)
    ctx = svc._format_context({"memories": [{"content": m["text"], "created_at": f'{m["days_ago"]} days ago'} for m in picks], "known_facts": []})
    sys_prompt = svc._build_system_prompt(ident)
    return {"sys": sys_prompt, "bare": svc._build_user_prompt("", q["text"]), "memory": svc._build_user_prompt(ctx, q["text"]),
            "mem_text": "\n".join(f'- ({m["days_ago"]}d ago) {m["text"]}' for m in p["memories"] if m["id"] in {x["id"] for x in picks}),
            "rel": [m["text"] for m in rel]}

class Runner:
    def __init__(self, ledger, client, mock):
        self.ledger, self.client, self.mock = ledger, client, mock
    async def call(self, model, system, user, max_tokens):
        cid = self.ledger.reserve(worst(model, system + user, max_tokens), model)   # durable BEFORE the call
        try:
            if self.mock:
                text = '{"a_uses_relevant_memory":0,"b_uses_relevant_memory":2,"a_wrong_or_stale_fact":false,"b_wrong_or_stale_fact":false,"a_natural_tone":1,"b_natural_tone":1,"winner":"B"}' if "compare two replies" in user else "mock reply"
                u_in, u_out = len((system + user).encode()) // 4, 50
            else:
                kw = {"system": system} if system else {}
                r = await self.client.messages.create(model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": user}], **kw)
                text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
                u_in, u_out = r.usage.input_tokens, r.usage.output_tokens
        except BaseException as e:
            self.ledger.mark_ambiguous(cid, repr(e)); print("call failed, counted at worst case:", repr(e)[:120], file=sys.stderr); return None
        pi, po = price(model)
        self.ledger.settle(cid, (u_in * pi + u_out * po) / 1e6, u_in, u_out)
        return text

async def run(args):
    rng = random.Random(args.seed)
    personas = [json.loads(l) for l in open(HERE / "data" / "personas.jsonl")]
    rng.shuffle(personas)
    cases = []
    svc = load_prompt_builders()
    kinds = args.kinds.split(",")
    for p in personas:
        if len(cases) >= args.cases: break
        k = kinds[len(cases) % len(kinds)]
        qs = [q for q in p["queries"] if q["kind"] == k]
        if not qs: continue
        q = rng.choice(qs)
        c = build_case(p, q, IDENT, svc, rng); c.update(pid=p["pid"], q=q["text"], kind=q["kind"]); cases.append(c)
    ledger = Ledger(args.ledger, float(os.environ.get("EXPERIMENT_TOTAL_CAP_USD", "0")), run_cap_usd=args.run_cap)
    client = None
    if not args.mock:
        from anthropic import AsyncAnthropic; client = AsyncAnthropic()
    R = Runner(ledger, client, args.mock)
    sem = asyncio.Semaphore(3)
    out = []
    async def one(c):
        async with sem:
            try:
                a = await R.call(REPLY_MODEL, c["sys"], c["bare"], 400)
                b = await R.call(REPLY_MODEL, c["sys"], c["memory"], 400)
                if a is None or b is None: return
                flip = rng.random() < 0.5
                A, B = (b, a) if flip else (a, b)
                j = await R.call(JUDGE_MODEL, "", JUDGE.format(mem=c["mem_text"], q=c["q"], kind=c["kind"], rel=c["rel"], a=A, b=B), 300)
                if j is None: return
                try:
                    s = j.strip(); s = s[s.index("{"): s.rindex("}") + 1]; d = json.loads(s)
                except Exception: print("unparseable judge (cost counted)", file=sys.stderr); return
                mem_is = "A" if flip else "B"
                w = d["winner"]; d["memory_won"] = None if w == "tie" else (w == mem_is)
                d.update(pid=c["pid"], kind=c["kind"], mem_arm=mem_is)
                out.append(d)
            except BudgetExceeded as e:
                print("skipped, budget:", e, file=sys.stderr)
    await asyncio.gather(*[one(c) for c in cases])
    n = len(out); won = sum(1 for d in out if d["memory_won"] is True); lost = sum(1 for d in out if d["memory_won"] is False)
    def sc(k): return sum(d[("b_" if d["mem_arm"] == "B" else "a_") + k] for d in out) / max(n, 1)
    def sb(k): return sum(d[("a_" if d["mem_arm"] == "B" else "b_") + k] for d in out) / max(n, 1)
    summ = {"cases": n, "memory_wins": won, "bare_wins": lost, "ties": n - won - lost,
            "mem_uses_relevant": round(sc("uses_relevant_memory"), 2), "bare_uses_relevant": round(sb("uses_relevant_memory"), 2),
            "mem_wrong_stale": sum(d[("b_" if d["mem_arm"] == "B" else "a_") + "wrong_or_stale_fact"] for d in out),
            "bare_wrong_stale": sum(d[("a_" if d["mem_arm"] == "B" else "b_") + "wrong_or_stale_fact"] for d in out),
            "ledger": ledger.summary(), "total_counted_usd": round(ledger.total_counted(), 4)}
    Path(args.out).write_text(json.dumps({"summary": summ, "rows": out}, indent=1))
    summ["caveat"] = "uncalibrated model judge, tiny n, oracle-context diagnostic (gold memories given), NOT retrieval or end-to-end; no quality claim"
    print(json.dumps(summ, indent=1))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=int, default=6); ap.add_argument("--kinds", default="correction,direct,advice")
    ap.add_argument("--seed", type=int, default=7); ap.add_argument("--run-cap", type=float, default=0.50)
    ap.add_argument("--ledger", default=str(HERE / "data" / "spend_ledger.sqlite")); ap.add_argument("--out", default=str(HERE / "data" / "conv_eval_results.json"))
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    if not a.mock:
        if os.environ.get("EXPERIMENT_PAID_RUN_APPROVED") != "yes": sys.exit("refusing paid run: needs EXPERIMENT_PAID_RUN_APPROVED=yes after owner approval")
        if "EXPERIMENT_TOTAL_CAP_USD" not in os.environ: sys.exit("set EXPERIMENT_TOTAL_CAP_USD")
    else:
        os.environ.setdefault("EXPERIMENT_TOTAL_CAP_USD", "1000")
    asyncio.run(run(a))
