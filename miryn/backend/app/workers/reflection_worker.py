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
    """
    llm = LLMService()
    engine = ReflectionEngine(llm)
    identity_engine = IdentityEngine()
    result = asyncio.run(engine.analyze_conversation(user_id=user_id, conversation=conversation))

    updates = {}
    
    # 1. Write emotions
    emotions = result.get("emotions") or {}
    if emotions.get("primary_emotion"):
        updates["emotions"] = [emotions]

    # 2. Write patterns
    patterns = result.get("patterns") or {}
    if patterns.get("topic_co_occurrences"):
        updates["patterns"] = [
            {
                "pattern_type": "topic_co_occurrence",
                "description": p.get("pattern", "<unknown>"),
                "confidence": min(p.get("frequency", 1) / 10, 1.0)
            }
            for p in patterns["topic_co_occurrences"]
            if p.get("pattern")
        ]

    # 3. Apply basic updates (emotions and patterns)
    if updates:
        identity_engine.update_identity(user_id, updates)

    # 4. Write open loops from all topics (importance and resolved state extracted per-topic)
    # We use a separate loop for track_open_loop because it handles its own merging logic
    # Note: In a future optimization, we could batch these into one update_identity call.
    for topic in result.get("topics", []):
        importance = topic.get("importance", 1) if isinstance(topic, dict) else 1
        identity_engine.track_open_loop(user_id, topic, importance=importance)

    publish_event(user_id, {"type": "reflection.ready", "payload": result})
    return result
