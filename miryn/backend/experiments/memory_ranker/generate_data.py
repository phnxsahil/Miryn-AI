"""Generate a FICTIONAL retrieval benchmark for Miryn's memory ranking. No real user data.

Each call asks a Claude model to invent one persona with ~24 remembered facts (with ages in days) and
8 queries whose relevant memories the generator names. The generator knows the labels because it wrote
the memories for the queries; labels are therefore model-made, not human-verified (see README).

Spend guard: stops before ANTHROPIC_EXPERIMENT_MAX_USD (default 1.00) using the API's reported usage.
Usage: ANTHROPIC_API_KEY=... python generate_data.py [n_personas] [start_index]  (appends to data/personas.jsonl, costs to personas.cost)
"""
import asyncio, json, os, random, sys
from pathlib import Path
from anthropic import AsyncAnthropic

MODEL = os.environ.get("EXPERIMENT_MODEL", "claude-haiku-5-5")
PRICE_IN, PRICE_OUT = 0.50, 2.50  # USD/MTok, higher Haiku 5.5 tier (conservative)
WORST = (4000 * 0.50 + 7000 * 2.50) / 1e6
MAX_USD = float(os.environ.get("ANTHROPIC_EXPERIMENT_MAX_USD", "1.00"))
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

async def one(client, seed, i, state, lock):
    async with lock:
        if state["spent"] + state["reserved"] + WORST > MAX_USD:
            return None
        state["reserved"] += WORST  # reserve worst case for this call
    try:
        r = await client.messages.create(model=MODEL, max_tokens=7000,
                                         messages=[{"role": "user", "content": PROMPT.format(seed=seed)}])
        u = r.usage
        actual = (u.input_tokens * PRICE_IN + u.output_tokens * PRICE_OUT) / 1e6
        async with lock:
            state["last_actual"] = state.get("last_actual", 0.0) + actual
        CALLS = OUT.with_name('calls.jsonl')
        def _log(ok, why=''):
            with CALLS.open('a') as cf:
                cf.write(json.dumps({'i': i, 'model': MODEL, 'in': u.input_tokens, 'out': u.output_tokens, 'est_usd': actual, 'ok': ok, 'why': why, 'stop': r.stop_reason}) + '\n')
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip()
        if text.startswith("```"):
            text = text.strip("`").split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            d = json.loads(text)
        except Exception as e:
            async with lock:
                _log(False, repr(e)[:80])
            raise
        d["seed"] = seed; d["pid"] = f"p{i:03d}"
        async with lock:  # persist immediately so a killed run loses nothing
            with OUT.open("a") as f:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
            with OUT.with_suffix(".cost").open("a") as f:
                f.write(f"{actual}\n")
            _log(True)
        return d, actual
    except Exception as e:
        print("fail", i, repr(e)[:120], file=sys.stderr)
        return None
    finally:
        async with lock:
            state["reserved"] -= WORST
            state["spent"] += state.pop("last_actual", 0.0)

async def main(n, start=0):
    random.seed(7)
    client = AsyncAnthropic()
    state = {"spent": 0.0, "reserved": 0.0}; lock = asyncio.Lock(); spent = 0.0
    seeds = [SEEDS[i % len(SEEDS)] + (f" (variation {i // len(SEEDS) + 1})" if i >= len(SEEDS) else "") for i in range(start, start + n)]
    sem = asyncio.Semaphore(10)
    async def run(i, s):
        async with sem:
            return await one(client, s, i, state, lock)
    results = await asyncio.gather(*[run(start + k, s) for k, s in enumerate(seeds)])
    ok = [r for r in results if r]
    for d, cost in ok:
        spent += cost
    print(f"personas {len(ok)}/{n}, actual spend ${spent:.4f}")

if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 60, int(sys.argv[2]) if len(sys.argv) > 2 else 0))
