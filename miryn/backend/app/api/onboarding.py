import logging
import sys
import json
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session
from app.core.security import get_current_user_id
from app.services.identity_engine import IdentityEngine
from app.schemas.onboarding import OnboardingCompleteRequest

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

identity_engine = IdentityEngine()
logger = logging.getLogger(__name__)


def _load_presets():
    presets_path = Path(__file__).resolve().parent.parent / "config" / "presets.json"
    with open(presets_path, "r", encoding="utf-8") as handle:
        presets = json.load(handle)

    for preset in presets:
        weights = preset.get("memory_weights") or {}
        total = sum(float(v) for v in weights.values()) if weights else 0.0
        if total and abs(total - 1.0) > 0.0001:
            preset["memory_weights"] = {k: float(v) / total for k, v in weights.items()}

    return presets


def _select_preset(presets, preset_id: str | None):
    if preset_id:
        match = next((p for p in presets if p.get("id") == preset_id), None)
        if match:
            return match
    return next((p for p in presets if p.get("id") == "companion"), presets[0])


@router.post("/complete")
def complete_onboarding(
    payload: OnboardingCompleteRequest,
    user_id: str = Depends(get_current_user_id),
):
    responses = payload.responses or []
    presets = _load_presets()
    preset = _select_preset(presets, payload.preset)

    if has_sql():
        with get_sql_session() as session:
            if responses:
                for r in responses:
                    session.execute(
                        text(
                            """
                            INSERT INTO onboarding_responses (user_id, question, answer)
                            VALUES (:user_id, :question, :answer)
                            """
                        ),
                        {"user_id": user_id, "question": r.question, "answer": r.answer},
                    )

            updated = identity_engine.update_identity(
                user_id,
                {
                    "state": "active",
                    "traits": preset.get("initial_traits", {}),
                    "values": preset.get("initial_values", {}),
                    "memory_weights": preset.get("memory_weights", {}),
                    "preset": payload.preset or "companion",
                },
                sql_session=session,
            )

        # record_belief must run AFTER the session commits to avoid a deadlock
        # (it opens its own session internally and would block on the uncommitted row)
        if payload.seed_belief:
            identity_engine.record_belief(
                user_id,
                topic="core_belief",
                belief=payload.seed_belief,
                confidence=0.8,
            )

        return {"status": "ok", "identity": updated}

    db = get_db()
    inserted_ids = []

    try:
        if responses:
            inserts = [
                {"user_id": user_id, "question": r.question, "answer": r.answer}
                for r in responses
            ]
            resp = db.table("onboarding_responses").insert(inserts).execute()
            inserted_ids = [row.get("id") for row in (resp.data or []) if row.get("id")]

        updated = identity_engine.update_identity(
            user_id,
            {
                "state": "active",
                "traits": preset.get("initial_traits", {}),
                "values": preset.get("initial_values", {}),
                "memory_weights": preset.get("memory_weights", {}),
                "preset": payload.preset or "companion",
            },
        )
        if payload.seed_belief:
            identity_engine.record_belief(
                user_id,
                topic="core_belief",
                belief=payload.seed_belief,
                confidence=0.8,
            )
    except Exception:
        original_exc = sys.exc_info()
        if inserted_ids:
            try:
                db.table("onboarding_responses").delete().in_("id", inserted_ids).execute()
            except Exception:
                logger.exception("Failed to rollback onboarding responses for user %s", user_id)
        if original_exc[1] is not None and original_exc[2] is not None:
            raise original_exc[1].with_traceback(original_exc[2])
        raise

    return {"status": "ok", "identity": updated}


@router.get("/presets")
def list_presets():
    presets = _load_presets()
    trimmed = [
        {
            "id": p.get("id"),
            "display_name": p.get("display_name"),
            "tagline": p.get("tagline"),
            "example_response": p.get("example_response"),
        }
        for p in presets
    ]
    return trimmed
