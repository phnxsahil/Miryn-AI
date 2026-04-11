"""
Analytics API - Divyadeep Kaur
Exposes emotion and identity analytics endpoints.
"""
from fastapi import APIRouter, Depends
from app.core.security import get_current_user_id
from app.services.emotion_analytics import emotion_analytics
from app.services.identity_analytics import identity_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/emotions")
async def get_emotion_analytics(
    days: int = 30,
    user_id: str = Depends(get_current_user_id),
):
    """
    Get emotion analytics for the authenticated user over the last N days.
    Returns mood score, volatility, trend, entropy and dominant emotions.
    """
    return emotion_analytics.analyze(user_id, days=days)


@router.get("/identity")
async def get_identity_analytics(
    user_id: str = Depends(get_current_user_id),
):
    """
    Get identity analytics for the authenticated user.
    Returns stability score, drift, total versions and version timeline.
    """
    return identity_analytics.analyze(user_id)


@router.get("/summary")
async def get_analytics_summary(
    days: int = 30,
    user_id: str = Depends(get_current_user_id),
):
    """
    Get a combined summary of emotion and identity analytics.
    """
    emotions = emotion_analytics.analyze(user_id, days=days)
    identity = identity_analytics.analyze(user_id)
    return {
        "emotions": emotions,
        "identity": identity,
    }