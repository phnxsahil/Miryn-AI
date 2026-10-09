"""Background worker for reflection tasks."""

import asyncio
import json
import logging
from app.services.reflection_engine import ReflectionEngine
from app.services.llm_service import LLMService
from app.services.identity_engine import IdentityEngine
from app.services.fact_store import FactStore
from app.services.importance import llm_is_usable, score_message_llm
from app.config import settings
from app.core.cache import publish_event
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="reflection.analyze")
def analyze_reflection(user_id: str, conversation: dict, source_message_id: str | None = None, user_message: str | None = None):
    """
    Run reflection analysis for a user's conversation and publish a readiness event.
    """
    if LLMService.quota_dead():
        logger.info("Skipping reflection task for user %s while Gemini quota cooldown is active", user_id)
        return {"entities": [], "emotions": {}, "topics": [], "patterns": {}, "insights": ""}

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

    source_text = user_message or conversation.get("user")
    if source_message_id and source_text and settings.IMPORTANCE_USE_LLM and llm_is_usable(llm) and not LLMService.quota_dead():
        try:
            refined_facts = asyncio.run(score_message_llm(llm, source_text))
            FactStore().replace_heuristic_for_message(user_id, source_message_id, refined_facts)
        except Exception:
            logger.warning("Importance LLM refinement failed for user %s", user_id)

    publish_event(user_id, {"type": "reflection.ready", "payload": result})
    # Celery's JSON serializer rejects datetimes
    return json.loads(json.dumps(result, default=str))
