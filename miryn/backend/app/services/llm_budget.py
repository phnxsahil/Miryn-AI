"""Persistent, shared spend ceiling for paid LLM calls made by Miryn's own code.

Scope: this ledger sees only calls routed through LLMService in this deployment's
database. It cannot see other uses of the same Anthropic key or account; set a
spend limit in the Anthropic console as the account-wide stop.

Every API worker, Celery worker and restart shares one row in the database, so
the ceiling holds across processes. A call first RESERVES its worst-case cost
(provable input bound + max output tokens) with a single atomic UPDATE that only
succeeds while spent + reserved + estimate <= cap. When the call finishes, the
reservation is settled to the actual usage the API reports.

Fails closed: no cap configured, no database, or any ledger error means the
call is refused. Reservations that are never settled (process killed mid-call)
stay counted, which errs on the side of spending less.
"""
from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import text

from app.config import settings

logger = logging.getLogger(__name__)

# One ledger row for the whole Anthropic account. Deliberately NOT keyed by model,
# key or price: switching model/config must never reset what was already spent.
PROVIDER = "anthropic"
# Fixed per-request token allowance for message framing and any hidden wrapper
# tokens the API adds on top of the serialized request.
_REQUEST_OVERHEAD_TOKENS = 1024

# USD per million tokens (input, output), from platform.claude.com/docs/en/about-claude/pricing
# as read 2026-11-02. Where a model has tiers the HIGHER tier is used. A model not
# listed here is refused unless ANTHROPIC_INPUT/OUTPUT_USD_PER_MTOK are both set.
MODEL_PRICES: dict[str, tuple[float, float]] = {
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-haiku-5-5": (0.50, 2.50),   # >100k-token prompt tier
    "claude-haiku-4-5-20251001": (1.0, 5.0),
}


class BudgetUnavailable(RuntimeError):
    """The spend ledger refused or could not be reached; callers must not spend."""


def _engine():
    from app.core.database import _db

    return _db.engine


def usd_to_micro(usd: float) -> int:
    return int(round(float(usd) * 1_000_000))


def prices_for(model: str) -> tuple[float, float]:
    """(input, output) USD per MTok for the model; fail closed when unknown."""
    inp, out = settings.ANTHROPIC_INPUT_USD_PER_MTOK, settings.ANTHROPIC_OUTPUT_USD_PER_MTOK
    if inp is not None and out is not None:
        return float(inp), float(out)
    if model in MODEL_PRICES:
        return MODEL_PRICES[model]
    raise BudgetUnavailable(f"no known price for model {model!r}; set ANTHROPIC_INPUT/OUTPUT_USD_PER_MTOK")


def estimate_micro(model: str, request_bytes: int, max_output_tokens: int) -> int:
    """Provable upper bound on one call's cost.

    Input: a token always covers at least one UTF-8 byte, so tokens <= bytes of the
    serialized request (system + messages), for any text, language or tokenizer;
    plus a fixed framing allowance. Output: at most max_tokens (thinking tokens
    count toward max_tokens). No prompt caching or tools are used by this adapter.
    """
    inp_price, out_price = prices_for(model)
    in_tokens = max(request_bytes, 0) + _REQUEST_OVERHEAD_TOKENS
    cost = in_tokens * inp_price + max(max_output_tokens, 0) * out_price  # USD/MTok == micro-USD/token
    return int(math.ceil(cost))


def actual_micro(model: str, usage: Any) -> Optional[int]:
    """Cost of a finished call from API usage. Cache tokens are billed at or below input price; counted at input price."""
    if usage is None:
        return None
    try:
        inp = int(getattr(usage, "input_tokens", 0) or 0)
        inp += int(getattr(usage, "cache_creation_input_tokens", 0) or 0) * 2  # 1h writes cost 2x input
        inp += int(getattr(usage, "cache_read_input_tokens", 0) or 0)
        out = int(getattr(usage, "output_tokens", 0) or 0)
    except (TypeError, ValueError):
        return None
    if inp == 0 and out == 0:
        return None
    inp_price, out_price = prices_for(model)
    return int(math.ceil(inp * inp_price + out * out_price))


@dataclass
class Reservation:
    micro: int
    model: str = ""
    done: bool = False


def _reserve_sync(est: int) -> None:
    cap = usd_to_micro(settings.ANTHROPIC_TOTAL_BUDGET_USD) - usd_to_micro(settings.ANTHROPIC_PRIOR_SPEND_USD)
    if usd_to_micro(settings.ANTHROPIC_TOTAL_BUDGET_USD) <= 0 or cap <= 0:
        raise BudgetUnavailable("ANTHROPIC_TOTAL_BUDGET_USD is not set")
    engine = _engine()
    if engine is None:
        raise BudgetUnavailable("no SQL database for the spend ledger")
    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO llm_budget (provider) VALUES (:p) ON CONFLICT (provider) DO NOTHING"),
                {"p": PROVIDER},
            )
            res = conn.execute(
                text(
                    "UPDATE llm_budget SET reserved_micro = reserved_micro + :e, updated_at = CURRENT_TIMESTAMP "
                    "WHERE provider = :p AND spent_micro + reserved_micro + :e <= :cap"
                ),
                {"p": PROVIDER, "e": est, "cap": cap},
            )
            if res.rowcount != 1:
                raise BudgetUnavailable("Claude budget ceiling reached")
    except BudgetUnavailable:
        raise
    except Exception as exc:
        raise BudgetUnavailable(f"spend ledger error: {exc}") from exc


def _settle_sync(reserved: int, spent: int) -> None:
    engine = _engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE llm_budget SET reserved_micro = reserved_micro - :r, spent_micro = spent_micro + :s, "
                "updated_at = CURRENT_TIMESTAMP WHERE provider = :p"
            ),
            {"p": PROVIDER, "r": reserved, "s": spent},
        )


async def reserve(model: str, request_bytes: int, max_output_tokens: int) -> Reservation:
    est = estimate_micro(model, request_bytes, max_output_tokens)
    await asyncio.to_thread(_reserve_sync, est)
    return Reservation(micro=est, model=model)


async def settle(res: Reservation, usage: Any = None, *, charged: bool = True) -> None:
    """Close a reservation. charged=False releases it (request was rejected before any generation)."""
    if res.done:
        return
    res.done = True
    if not charged:
        spent = 0
    else:
        actual = actual_micro(res.model, usage)
        # Unknown usage: keep the full worst-case estimate counted.
        spent = res.micro if actual is None else actual
    try:
        await asyncio.to_thread(_settle_sync, res.micro, spent)
    except Exception:
        logger.exception("Claude spend ledger settle failed; reservation stays counted")
