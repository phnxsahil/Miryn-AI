"""Background worker for reflection tasks."""

import asyncio
from app.services.reflection_engine import ReflectionEngine
from app.services.llm_service import LLMService
from app.services.identity_engine import IdentityEngine
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
    identity_engine = IdentityEngine()
    result = asyncio.run(engine.analyze_conversation(user_id=user_id, conversation=conversation))

    emotions = result.get("emotions") or {}
    if emotions.get("primary_emotion"):
        identity_engine.update_identity(user_id, {"emotions": [emotions]})

    patterns = result.get("patterns") or {}
    for item in patterns.get("topic_co_occurrences", []):
        topics = item.get("topics") or []
        if topics:
            identity_engine.track_open_loop(user_id, topics[0], importance=item.get("frequency", 1))

    temporal_patterns = patterns.get("temporal_emotional_patterns", [])
    if temporal_patterns:
        current_patterns = identity_engine.get_identity(user_id).get("patterns", [])
        for item in temporal_patterns:
            updated_patterns = list(current_patterns)
            updated_patterns.append(item)
            identity_engine.update_identity(user_id, {"patterns": updated_patterns})
            current_patterns = updated_patterns

    publish_event(user_id, {"type": "reflection.ready", "payload": result})
    return result
