"""
Analytics API
Exposes emotion and identity analytics endpoints.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
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
