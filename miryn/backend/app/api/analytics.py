"""
Analytics API
Exposes emotion and identity analytics endpoints.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from app.core.security import get_current_user_id

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/emotions")
async def get_emotion_analytics(
    days: int = Query(30, ge=1, le=365),
    user_id: str = Depends(get_current_user_id),
):
    """
    Placeholder for emotion analytics — returns empty results until an analytics
    frontend is built.
    """
    # ponytail: emotion_analytics.py was removed (dead code, no frontend consumer).
    # When an analytics dashboard exists, wire this to real data.
    return {
        "message": "Emotion analytics not yet implemented.",
        "mood_score": None,
        "volatility": None,
        "trend": None,
        "entropy": None,
        "dominant_emotions": [],
    }


@router.get("/identity")
async def get_identity_analytics(
    user_id: str = Depends(get_current_user_id),
):
    """
    Placeholder for identity analytics — returns empty results until an analytics
    frontend is built.
    """
    return {
        "message": "Identity analytics not yet implemented.",
        "stability_score": None,
        "drift": None,
        "total_versions": 0,
        "version_timeline": [],
    }


@router.get("/summary")
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365),
    user_id: str = Depends(get_current_user_id),
):
    """Combined summary placeholder."""
    return {
        "emotions": {"message": "Not yet implemented."},
        "identity": {"message": "Not yet implemented."},
    }


# Separate from personal emotion/identity routes. Disabled until the owner explicitly
# configures a server-only user-ID allowlist. Never authorize by an email supplied by a client.
def require_analytics_owner(user_id: str = Depends(get_current_user_id)) -> str:
    from app.config import settings
    allowed = {value.strip() for value in settings.ANALYTICS_OWNER_USER_IDS.split(",") if value.strip()}
    if user_id not in allowed:
        raise HTTPException(status_code=403, detail="Owner analytics access is not enabled for this account.")
    return user_id


@router.get("/owner")
def get_owner_analytics(
    response: Response,
    days: int = Query(30, ge=1, le=90),
    owner_id: str = Depends(require_analytics_owner),
):
    from app.core.database import get_sql_session, has_sql
    from app.services.owner_metrics import read_account_metrics
    response.headers["Cache-Control"] = "no-store, private"
    if not has_sql():
        raise HTTPException(status_code=503, detail="Account metrics database is unavailable.")
    with get_sql_session() as session:
        return read_account_metrics(session, days=days)
