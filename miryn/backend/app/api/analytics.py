"""
Analytics API - Divyadeep Kaur
Exposes emotion and identity analytics endpoints.
"""
from fastapi import APIRouter, Depends
from app.core.security import get_current_user_id
from app.services.emotion_analytics import emotion_analytics

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