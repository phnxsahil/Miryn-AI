from typing import Dict
import asyncio
import logging
from app.services.identity_engine import IdentityEngine
from app.services.memory_layer import MemoryLayer
from app.services.reflection_engine import ReflectionEngine
from app.services.llm_service import LLMService
from app.core.cache import publish_event
from app.workers.reflection_worker import analyze_reflection
from app.config import settings
from app.services.ds_service import ds_service


class ConversationOrchestrator:
    def __init__(self):
        self.llm = LLMService()
        self.memory = MemoryLayer()
        self.reflection = ReflectionEngine(self.llm)
        self.identity = IdentityEngine(reflection=self.reflection)
        self.logger = logging.getLogger(__name__)

    async def handle_message(self, user_id: str, message: str, conversation_id: str) -> Dict:
        """
        Process an incoming user message through identity, memory, LLM, and reflection pipelines and return the assistant response along with derived insights and any detected identity conflicts.

        Returns:
            result (Dict): A dictionary with keys:
                - "response" (str): The assistant's reply, or a fallback message if LLM generation failed.
                - "insights" (Dict): Reflection analysis results for the conversation.
                - "conflicts" (List): Any identity conflicts detected for the user's message.
                - "entities" (List): Named entities extracted from the user message.
                - "emotions" (Dict): Emotions detected in the user message.
        """
        identity = self.identity.get_identity(user_id)

        memories = []
        try:
            memories = await asyncio.wait_for(
                self.memory.retrieve_context(
                    user_id=user_id,
                    query=message,
                    limit=5,
                    strategy="hybrid",
                    conversation_id=conversation_id,
                ),
                timeout=settings.CONTEXT_RETRIEVAL_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            self.logger.warning("Context retrieval timed out for user %s", user_id)
        except Exception:
            self.logger.exception("Context retrieval failed for user %s", user_id)

        context = {
            "identity": identity,
            "memories": memories,
            "patterns": {},
        }

        def _fire_and_forget(coro, label: str):
            task = asyncio.create_task(coro)

            def _done(t: asyncio.Task):
                try:
                    t.result()
                except Exception:
                    self.logger.exception("%s task failed for user %s", label, user_id)

            task.add_done_callback(_done)

        _fire_and_forget(
            self.memory.store_conversation(
                user_id=user_id,
                role="user",
                content=message,
                conversation_id=conversation_id,
            ),
            "store_user_message",
        )

        conflicts = []
        if settings.ENABLE_INLINE_CONFLICT_DETECTION:
            try:
                conflicts = await asyncio.wait_for(
                    self.identity.detect_conflicts(user_id, message),
                    timeout=settings.CONFLICT_DETECTION_TIMEOUT_SECONDS,
                )
                if conflicts:
                    self.identity.add_conflicts(user_id, conflicts)
                    await asyncio.to_thread(publish_event, user_id, {"type": "identity.conflict", "payload": conflicts})
            except asyncio.TimeoutError:
                self.logger.warning("Conflict detection timed out for user %s", user_id)
            except Exception:
                self.logger.exception("Conflict detection failed for user %s", user_id)
        else:
            async def _detect_conflicts_bg():
                try:
                    detected = await asyncio.wait_for(
                        self.identity.detect_conflicts(user_id, message),
                        timeout=settings.CONFLICT_DETECTION_TIMEOUT_SECONDS,
                    )
                    if detected:
                        self.identity.add_conflicts(user_id, detected)
                        await asyncio.to_thread(
                            publish_event,
                            user_id,
                            {"type": "identity.conflict", "payload": detected},
                        )
                except Exception:
                    self.logger.exception("Background conflict detection failed for user %s", user_id)

            _fire_and_forget(_detect_conflicts_bg(), "conflict_detection")

        try:
            response = await asyncio.wait_for(
                self.llm.chat(
                    context=context,
                    user_message=message,
                    identity=identity,
                ),
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            self.logger.warning("LLM timed out for user %s", user_id)
            fallback = "I'm taking longer than usual to respond. Please try again in a moment."
            _fire_and_forget(
                self.memory.store_conversation(
                    user_id=user_id,
                    role="assistant",
                    content=fallback,
                    conversation_id=conversation_id,
                ),
                "store_timeout_fallback",
            )
            return {
                "response": fallback,
                "insights": {},
                "conflicts": [],
                "entities": [],
                "emotions": {},
            }
        except Exception:
            self.logger.exception("LLM chat failed for user %s", user_id)
            fallback = "I'm having trouble responding right now. Please try again shortly."
            try:
                _fire_and_forget(
                    self.memory.store_conversation(
                        user_id=user_id,
                        role="assistant",
                        content=fallback,
                        conversation_id=conversation_id,
                    ),
                    "store_llm_error_fallback",
                )
            except Exception:
                self.logger.exception("Failed to queue fallback assistant message for user %s", user_id)
            return {
                "response": fallback,
                "insights": {},
                "conflicts": [],
                "entities": [],
                "emotions": {},
            }

        _fire_and_forget(
            self.memory.store_conversation(
                user_id=user_id,
                role="assistant",
                content=response,
                conversation_id=conversation_id,
            ),
            "store_assistant_message",
        )

        conversation_data = {"user": message, "assistant": response}

        # DS Service — run concurrently off the event loop
        entities, emotions = await asyncio.gather(
            asyncio.to_thread(ds_service.extract_entities, message),
            asyncio.to_thread(ds_service.detect_emotions, message),
        )

        insights: Dict = {}

        # Queue reflection asynchronously via Celery instead of running inline
        # to avoid duplicate LLM calls and cost.
        try:
            await asyncio.to_thread(analyze_reflection.delay, user_id, conversation_data)
            await asyncio.to_thread(publish_event, user_id, {"type": "reflection.queued"})
        except Exception:
            self.logger.exception("Failed to queue reflection task for user %s", user_id)
            if settings.ENABLE_REFLECTION_SYNC_FALLBACK:
                try:
                    insights = await asyncio.wait_for(
                        self.reflection.analyze_conversation(
                            user_id=user_id,
                            conversation=conversation_data,
                        ),
                        timeout=settings.LLM_TIMEOUT_SECONDS,
                    )
                except Exception:
                    self.logger.exception("Reflection analysis fallback failed for user %s", user_id)
            else:
                await asyncio.to_thread(publish_event, user_id, {"type": "reflection.skipped"})

        return {
            "response": response,
            "insights": insights,
            "conflicts": conflicts,
            "entities": entities,
            "emotions": emotions,
        }