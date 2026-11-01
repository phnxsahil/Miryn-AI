"""Generate a FICTIONAL retrieval benchmark for Miryn's memory ranking. No real user data.

Each call asks a Claude model to invent one persona with ~24 remembered facts (with ages in days) and
8 queries whose relevant memories the generator names. The generator knows the labels because it wrote
the memories for the queries; labels are therefore model-made, not human-verified (see README).

Spend guard: durable pre-call reservations in data/spend_ledger.sqlite (see spend_ledger.py); refuses to run without EXPERIMENT_PAID_RUN_APPROVED=yes and EXPERIMENT_TOTAL_CAP_USD.
Usage: ANTHROPIC_API_KEY=... python generate_data.py [n_personas] [start_index]  (appends to data/personas.jsonl, costs to personas.cost)
"""
import asyncio, json, os, random, sys
from pathlib import Path

MODEL = os.environ.get("EXPERIMENT_MODEL", "claude-haiku-5-5")
PRICE_IN, PRICE_OUT = 0.50, 2.50  # USD/MTok, higher Haiku 5.5 tier (conservative)
OUT = Path(__file__).parent / "data" / "personas.jsonl"

SEEDS = ["nurse on night shifts", "college student in Pune", "freelance illustrator", "retired teacher", "startup founder",
         "new parent", "marathon runner", "software tester", "farmer turned shopkeeper", "grad student in chemistry",
         "chef", "long-distance couple", "musician", "accountant changing careers", "caregiver for a parent",
         "gamer and streamer", "bank clerk", "architect", "high-school teacher", "taxi driver", "yoga instructor",
         "journalist", "pharmacist", "carpenter", "data analyst", "wedding planner", "immigrant in a new city",
         "recovering from an injury", "bookshop owner", "game designer"]

PROMPT = """Invent ONE fictional person: {seed}. Make names, places and details up; nothing real.
Return ONLY JSON (no markdown) with this shape:
{{"persona": "one line",
 "memories": [{{"id": "m1", "text": "a fact a companion app would have stored, first person or neutral, 8-25 words", "category": "work|health|family|preference|event|goal|emotion|other", "days_ago": 0}}],
 "queries": [{{"text": "what the user says now", "kind": "direct|paraphrase|recent|advice|correction", "relevant": ["m3"]}}]}}
Rules:
- 24 memories, ids m1..m24, days_ago spread between 0 and 400 (several within 7 days, several over 200).
- Include distractors: topically similar but irrelevant memories (same subject, different detail).
- 8 queries, kinds: 2 direct (shares words with the memory), 2 paraphrase (NO shared key words with the relevant memory), 1 recent (about how things are going lately, relevant memories must be the recent ones), 2 advice (user asks for advice; relevant = memories that should shape it), 1 correction (an older memory was later contradicted by a newer one; relevant = only the newer one).
- Each query has 1-3 relevant ids. Mix in 1 Hinglish query if natural.
- Memories must be consistent with their days_ago ordering."""

def worst_case_usd(prompt, max_tokens):
    # input bound: bytes of prompt (tokens <= bytes) + 1024 overhead; output bound: max_tokens
    return ((len(prompt.encode()) + 1024) * PRICE_IN + max_tokens * PRICE_OUT) / 1e6

async def one(client, seed, i, ledger):
    prompt = PROMPT.format(seed=seed)
    cid = ledger.reserve(worst_case_usd(prompt, 7000), MODEL)  # durable BEFORE the call; raises BudgetExceeded
    try:
        r = await client.messages.create(model=MODEL, max_tokens=7000, messages=[{"role": "user", "content": prompt}])
    except BaseException as e:  # network error, timeout, cancel: billing unknown, reservation stays counted
        ledger.mark_ambiguous(cid, repr(e))
        print("call failed (counted at worst case)", i, repr(e)[:100], file=sys.stderr)
        return None
    u = r.usage
    actual = (u.input_tokens * PRICE_IN + u.output_tokens * PRICE_OUT) / 1e6
    ledger.settle(cid, actual, u.input_tokens, u.output_tokens)
    try:
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip()
        if text.startswith("```"):
            text = text.strip("`").split("\n", 1)[1].rsplit("```", 1)[0]
        d = json.loads(text)
    except Exception as e:  # response arrived and was billed (settled); content unusable
        print("unparseable response (cost counted)", i, repr(e)[:100], file=sys.stderr)
        return None
    d["seed"] = seed; d["pid"] = f"p{i:03d}"
    with OUT.open("a") as f:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")
    return d, actual

async def main(n, start=0):
    if os.environ.get("EXPERIMENT_PAID_RUN_APPROVED") != "yes":
        sys.exit("refusing paid run: set EXPERIMENT_PAID_RUN_APPROVED=yes only after the owner approves this batch")
    cap = os.environ.get("EXPERIMENT_TOTAL_CAP_USD")
    if cap is None:
        sys.exit("set EXPERIMENT_TOTAL_CAP_USD (total cap for this ledger, including prior spend rows)")
    from spend_ledger import Ledger, BudgetExceeded
    ledger = Ledger(Path(__file__).parent / "data" / "spend_ledger.sqlite", float(cap),
                    run_cap_usd=float(os.environ.get("EXPERIMENT_RUN_CAP_USD", "0.25")))
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic()
    seeds = [SEEDS[i % len(SEEDS)] + (f" (variation {i // len(SEEDS) + 1})" if i >= len(SEEDS) else "") for i in range(start, start + n)]
    sem = asyncio.Semaphore(5)
    async def run(i, s):
        async with sem:
            try:
                return await one(client, s, i, ledger)
            except BudgetExceeded as e:
                print("skipped, budget:", e, file=sys.stderr)
                return None
    results = await asyncio.gather(*[run(start + k, s) for k, s in enumerate(seeds)])
    print(f"personas {len([r for r in results if r])}/{n}; ledger {ledger.summary()}; total counted ${ledger.total_counted():.4f}")

if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 60, int(sys.argv[2]) if len(sys.argv) > 2 else 0))
