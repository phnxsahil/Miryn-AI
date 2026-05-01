"""
Analytics API - Divyadeep Kaur
Exposes emotion and identity analytics endpoints.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.security import get_current_user_id
from app.services.demo_compare_service import demo_compare_service
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
    return await asyncio.to_thread(emotion_analytics.analyze, user_id, days)


@router.get("/identity")
async def get_identity_analytics(
    user_id: str = Depends(get_current_user_id),
):
    """
    Get identity analytics for the authenticated user.
    Returns stability score, drift, total versions and version timeline.
    """
    return await asyncio.to_thread(identity_analytics.analyze, user_id)


@router.get("/summary")
async def get_analytics_summary(
    days: int = 30,
    user_id: str = Depends(get_current_user_id),
):
    """
    Get a combined summary of emotion and identity analytics.
    """
    emotions, identity = await asyncio.gather(
        asyncio.to_thread(emotion_analytics.analyze, user_id, days),
        asyncio.to_thread(identity_analytics.analyze, user_id),
    )
    return {
        "emotions": emotions,
        "identity": identity,
    }


@router.get("/demo/personas")
def get_demo_personas(user_id: str = Depends(get_current_user_id)):
    del user_id
    try:
        return {"personas": demo_compare_service.list_demo_personas()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/demo/seed")
def seed_demo_personas(user_id: str = Depends(get_current_user_id)):
    del user_id
    try:
        return demo_compare_service.seed_demo_personas()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/demo/persona/{persona_user_id}")
def get_demo_persona_detail(
    persona_user_id: str,
    user_id: str = Depends(get_current_user_id),
):
    del user_id
    try:
        return demo_compare_service.get_persona_detail(persona_user_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/compare")
def get_comparison(
    left_user_id: str = Query(...),
    right_user_id: str = Query(...),
    user_id: str = Depends(get_current_user_id),
):
    del user_id
    try:
        return demo_compare_service.compare_users(left_user_id, right_user_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/report")
def get_comparison_report(
    left_user_id: str = Query(...),
    right_user_id: str = Query(...),
    user_id: str = Depends(get_current_user_id),
):
    del user_id
    try:
        return demo_compare_service.build_report(left_user_id, right_user_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
