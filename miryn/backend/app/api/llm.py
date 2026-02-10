"""Routes exposing configured LLM metadata."""

from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/models")
def list_models():
    """
    Returns configured model info. For Vertex, this is the model string in env.
    """
    return {
        "provider": settings.LLM_PROVIDER,
        "model": settings.VERTEX_MODEL if settings.LLM_PROVIDER == "vertex" else settings.GEMINI_MODEL,
        "vertex_project_id": settings.VERTEX_PROJECT_ID if settings.LLM_PROVIDER == "vertex" else None,
        "vertex_location": settings.VERTEX_LOCATION if settings.LLM_PROVIDER == "vertex" else None,
    }
