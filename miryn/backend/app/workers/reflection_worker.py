"""Background worker for reflection tasks."""

import asyncio
from app.services.reflection_engine import ReflectionEngine
from app.services.llm_service import LLMService
from app.core.cache import publish_event
from app.workers.celery_app import celery_app


@celery_app.task(name="reflection.analyze")
def analyze_reflection(user_id: str, conversation: dict):
    llm = LLMService()
    engine = ReflectionEngine(llm)
    result = asyncio.run(engine.analyze_conversation(user_id=user_id, conversation=conversation))
    publish_event(user_id, {"type": "reflection.ready", "payload": result})
    return result
