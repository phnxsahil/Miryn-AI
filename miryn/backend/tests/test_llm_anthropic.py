import asyncio
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, text

from app.config import settings
from app.services import llm_budget
from app.services.llm_service import LLMService, QuotaExhausted
from app.services.safety import BLOCKED_REPLY

pytestmark = pytest.mark.live_llm  # the client is faked below; no network


class RateLimitError(Exception):
    status_code = 429


class BadRequestError(Exception):
    status_code = 400


def _usage(i=100, o=50):
    return SimpleNamespace(input_tokens=i, output_tokens=o)


def _ok(text_="hi", stop="end_turn", usage=None):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text_)], stop_reason=stop,
                           usage=usage or _usage())


@pytest.fixture
def ledger(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'b.db'}")
    with engine.begin() as c:
        c.execute(text((__import__("pathlib").Path(__file__).parents[1] / "migrations/014_llm_budget.sql").read_text()))
    monkeypatch.setattr(llm_budget, "_engine", lambda: engine)
    monkeypatch.setattr(settings, "ANTHROPIC_TOTAL_BUDGET_USD", 1.0)
    monkeypatch.setattr(settings, "ANTHROPIC_INPUT_USD_PER_MTOK", 2.0)
    monkeypatch.setattr(settings, "ANTHROPIC_OUTPUT_USD_PER_MTOK", 10.0)

    def row():
        with engine.begin() as c:
            return c.execute(text("SELECT spent_micro, reserved_micro FROM llm_budget")).one()
    return SimpleNamespace(engine=engine, row=row)


def _svc(monkeypatch, create=None, stream_factory=None):
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "test-key-not-real")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(settings, "ANTHROPIC_MODEL", "claude-test-model")
    svc = LLMService()
    svc.client = SimpleNamespace(messages=SimpleNamespace(create=create, stream=stream_factory))
    return svc


def test_model_comes_from_settings(monkeypatch):
    assert _svc(monkeypatch).model == "claude-test-model"


def test_generate_settles_to_actual_usage(monkeypatch, ledger):
    async def create(**kw):
        assert kw["model"] == "claude-test-model"
        return _ok(usage=_usage(1000, 500))
    assert asyncio.run(_svc(monkeypatch, create=create).generate("p", max_tokens=1000)) == "hi"
    # 1000*2 + 500*10 micro-USD, reservation fully released
    assert tuple(ledger.row()) == (7000, 0)


def test_text_blocks_skip_thinking_blocks(monkeypatch, ledger):
    async def create(**kw):
        r = _ok()
        r.content = [SimpleNamespace(type="thinking", thinking="..."), SimpleNamespace(type="text", text="answer")]
        return r
    assert asyncio.run(_svc(monkeypatch, create=create).generate("p")) == "answer"


def test_refusal_returns_blocked_reply(monkeypatch, ledger):
    async def create(**kw):
        return _ok(stop="refusal")
    assert asyncio.run(_svc(monkeypatch, create=create).generate("p")) == BLOCKED_REPLY


def test_rate_limit_is_busy_and_not_charged(monkeypatch, ledger):
    async def create(**kw):
        raise RateLimitError("slow down")
    with pytest.raises(QuotaExhausted):
        asyncio.run(_svc(monkeypatch, create=create).generate("p"))
    assert tuple(ledger.row()) == (0, 0)


def test_http_error_released_but_unknown_failure_stays_charged(monkeypatch, ledger):
    async def bad(**kw):
        raise BadRequestError("nope")
    with pytest.raises(BadRequestError):
        asyncio.run(_svc(monkeypatch, create=bad).generate("p", max_tokens=100))
    assert tuple(ledger.row()) == (0, 0)

    async def boom(**kw):
        raise ConnectionError("dropped mid flight")
    with pytest.raises(ConnectionError):
        asyncio.run(_svc(monkeypatch, create=boom).generate("p", max_tokens=100))
    spent, reserved = ledger.row()
    assert spent > 0 and reserved == 0  # worst-case estimate kept


def test_ceiling_refuses_before_calling(monkeypatch, ledger):
    called = []

    async def create(**kw):
        called.append(1)
        return _ok(usage=_usage(10, 10))
    monkeypatch.setattr(settings, "ANTHROPIC_TOTAL_BUDGET_USD", 0.005)  # 5000 micro
    svc = _svc(monkeypatch, create=create)
    with pytest.raises(QuotaExhausted):  # worst case 1000*10 = 10000 > cap
        asyncio.run(svc.generate("p", max_tokens=1000))
    assert not called
    assert asyncio.run(svc.generate("p", max_tokens=100)) == "hi"  # worst case ~1000 fits
    assert len(called) == 1


def test_concurrent_reservations_cannot_exceed_cap(monkeypatch, ledger):
    monkeypatch.setattr(settings, "ANTHROPIC_TOTAL_BUDGET_USD", 0.01)  # 10000 micro

    async def run():
        async def one():
            try:
                await llm_budget.reserve("m", 0, 100)  # (1024*2 + 100*10) = 3048 micro each
                return True
            except llm_budget.BudgetUnavailable:
                return False
        return await asyncio.gather(*[one() for _ in range(8)])
    results = asyncio.run(run())
    assert sum(results) == 3
    assert tuple(ledger.row()) == (0, 3 * 3048)


def test_fails_closed_without_cap_or_ledger(monkeypatch):
    async def create(**kw):
        raise AssertionError("must not be called")
    svc = _svc(monkeypatch, create=create)
    monkeypatch.setattr(settings, "ANTHROPIC_TOTAL_BUDGET_USD", 0.0)
    with pytest.raises(QuotaExhausted):
        asyncio.run(svc.generate("p"))
    monkeypatch.setattr(settings, "ANTHROPIC_TOTAL_BUDGET_USD", 1.0)
    monkeypatch.setattr(llm_budget, "_engine", lambda: None)
    with pytest.raises(QuotaExhausted):
        asyncio.run(svc.generate("p"))


def test_stream_settles_and_handles_refusal(monkeypatch, ledger):
    class Stream:
        def __init__(self, stop): self.stop = stop
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        @property
        def text_stream(self):
            async def it():
                yield "a"; yield "b"
            return it()
        async def get_final_message(self):
            return SimpleNamespace(stop_reason=self.stop, usage=_usage(100, 20))

    async def collect(svc):
        return [c async for c in svc.stream_chat({}, "hello there", {})]

    ok = _svc(monkeypatch, stream_factory=lambda **kw: Stream("end_turn"))
    assert asyncio.run(collect(ok)) == ["a", "b"]
    assert tuple(ledger.row()) == (400, 0)
    ref = _svc(monkeypatch, stream_factory=lambda **kw: Stream("refusal"))
    assert asyncio.run(collect(ref))[-1] == BLOCKED_REPLY


def test_stream_abandoned_midway_keeps_worst_case(monkeypatch, ledger):
    class Stream:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        @property
        def text_stream(self):
            async def it():
                yield "a"; yield "b"
            return it()
        async def get_final_message(self):
            raise AssertionError

    async def first_only(svc):
        gen = svc.stream_chat({}, "hello there", {})
        async for _ in gen:
            break
        await gen.aclose()
    asyncio.run(first_only(_svc(monkeypatch, stream_factory=lambda **kw: Stream())))
    spent, reserved = ledger.row()
    assert reserved == 0 and spent > 1000


def test_input_bound_covers_token_heavy_unicode(monkeypatch):
    """A token covers >=1 UTF-8 byte, so the byte bound holds even for worst-case text."""
    monkeypatch.setattr(settings, "ANTHROPIC_INPUT_USD_PER_MTOK", 2.0)
    monkeypatch.setattr(settings, "ANTHROPIC_OUTPUT_USD_PER_MTOK", 10.0)
    import json
    for text_ in ["a" * 5000, "\u4f60\u597d" * 2000, "\U0001F600" * 3000, "\u0928\u092e\u0938\u094d\u0924\u0947 " * 800,
                  "".join(chr(0x300 + (i % 60)) for i in range(5000)), "{}[]\\\"" * 2000]:
        raw = json.dumps({"system": "", "messages": [{"role": "user", "content": text_}]}, ensure_ascii=False).encode()
        worst_tokens = len(text_.encode("utf-8"))  # absolute ceiling: one token per byte
        est = llm_budget.estimate_micro("m", len(raw), 0)
        assert est >= worst_tokens * 2.0


def test_unknown_model_fails_closed_and_known_models_have_prices(monkeypatch, ledger):
    monkeypatch.setattr(settings, "ANTHROPIC_INPUT_USD_PER_MTOK", None)
    monkeypatch.setattr(settings, "ANTHROPIC_OUTPUT_USD_PER_MTOK", None)
    assert llm_budget.prices_for("claude-sonnet-5-5") == (2.0, 10.0)
    with pytest.raises(llm_budget.BudgetUnavailable):
        llm_budget.prices_for("claude-future-9")

    async def create(**kw):
        raise AssertionError("must not be called")
    svc = _svc(monkeypatch, create=create)  # sets model claude-test-model (not in table)
    with pytest.raises(QuotaExhausted):
        asyncio.run(svc.generate("p"))


def test_model_switch_does_not_reset_ledger(monkeypatch, ledger):
    async def create(**kw):
        return _ok(usage=_usage(1000, 500))
    asyncio.run(_svc(monkeypatch, create=create).generate("p", max_tokens=1000))
    monkeypatch.setattr(settings, "ANTHROPIC_MODEL", "other-model")
    svc = _svc(monkeypatch, create=create)
    monkeypatch.setattr(settings, "ANTHROPIC_MODEL", "yet-another")
    asyncio.run(_svc(monkeypatch, create=create).generate("p", max_tokens=1000))
    assert ledger.row()[0] == 14000
    with ledger.engine.begin() as c:
        assert c.execute(text("SELECT count(*) FROM llm_budget")).scalar() == 1


def test_prior_spend_is_deducted_from_cap(monkeypatch, ledger):
    monkeypatch.setattr(settings, "ANTHROPIC_TOTAL_BUDGET_USD", 0.01)  # 10000 micro
    monkeypatch.setattr(settings, "ANTHROPIC_PRIOR_SPEND_USD", 0.0099)  # leaves 100 micro
    with pytest.raises(llm_budget.BudgetUnavailable):
        asyncio.run(llm_budget.reserve("m", 0, 100))  # needs 3048
    monkeypatch.setattr(settings, "ANTHROPIC_PRIOR_SPEND_USD", 0.02)  # prior exceeds cap
    with pytest.raises(llm_budget.BudgetUnavailable):
        asyncio.run(llm_budget.reserve("m", 0, 1))
