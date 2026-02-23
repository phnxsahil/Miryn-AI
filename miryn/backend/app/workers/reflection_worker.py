"""Background worker for reflection tasks."""

import asyncio
from app.services.reflection_engine import ReflectionEngine
from app.services.llm_service import LLMService
from app.core.cache import publish_event
from app.workers.celery_app import celery_app


@celery_app.task(name="reflection.analyze")
def analyze_reflection(user_id: str, conversation: dict):
    """
    Run reflection analysis for a user's conversation and publish a readiness event.
    
    Performs a reflection analysis of `conversation` for `user_id`, publishes a "reflection.ready" event containing the analysis result for the user, and returns the analysis.
    
    Parameters:
        user_id (str): Identifier for the user whose conversation is analyzed.
        conversation (dict): Conversation data to analyze (structured messages/context).
    
    Returns:
        dict: Reflection analysis result payload.
    """
    llm = LLMService()
    engine = ReflectionEngine(llm)
    result = asyncio.run(engine.analyze_conversation(user_id=user_id, conversation=conversation))
    publish_event(user_id, {"type": "reflection.ready", "payload": result})
    return result
