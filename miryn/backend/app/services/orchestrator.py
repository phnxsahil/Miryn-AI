import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from app.config import settings
from app.core.cache import publish_event
from app.services.ds_service import ds_service
from app.services.identity_engine import IdentityEngine
from app.services.llm_service import LLMService
from app.services.memory_layer import MemoryLayer
from app.services.reflection_engine import ReflectionEngine
from app.workers.reflection_worker import analyze_reflection


class ConversationOrchestrator:
    def __init__(self):
        self.llm = LLMService()
        self.memory = MemoryLayer()
        self.reflection = ReflectionEngine(self.llm)
        self.identity = IdentityEngine(reflection=self.reflection)
        self.logger = logging.getLogger(__name__)

    async def handle_message(
        self,
        user_id: str,
        message: str,
        conversation_id: str,
        idempotency_key: str | None = None,
        sql_session: Any | None = None,
    ) -> Dict:
        """
        Process an incoming user message through identity, memory, LLM, and reflection pipelines and return the assistant response along with derived insights and any detected identity conflicts.

        Parameters:
            user_id (str): Identifier of the user sending the message.
            message (str): The incoming user message content.
            conversation_id (str): Conversation identifier used to scope retrieval and persistence.
            idempotency_key (str | None): Optional retry/deduplication key. When provided, completed results for the same user/conversation/key are reused and persisted message writes use deterministic idempotency keys.
            sql_session (Any | None): Optional open SQLAlchemy-like session reused for memory reads/writes. When None, downstream services open their own sessions as needed.

        Returns:
            result (Dict): A dictionary with keys:
                - "response" (str): The assistant's reply, or a fallback message if LLM generation failed.
                - "insights" (Dict): Reflection analysis results for the conversation.
                - "conflicts" (List): Any identity conflicts detected for the user's message.
                - "entities" (List): Named entities extracted from the user message.
                - "emotions" (Dict): Emotions detected in the user message.
        """
        cached_result = self._get_cached_result(user_id, conversation_id, idempotency_key)
        if cached_result is not None:
            self.logger.info(
                "Returning cached idempotent response for user %s conversation %s",
                user_id,
                conversation_id,
            )
            return cached_result

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
                    sql_session=sql_session,
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

        conflicts = []
        if settings.ENABLE_INLINE_CONFLICT_DETECTION:
            try:
                conflicts = await asyncio.wait_for(
                    self.identity.detect_conflicts(user_id, message),
                    timeout=settings.CONFLICT_DETECTION_TIMEOUT_SECONDS,
                )
                if conflicts:
                    self.identity.add_conflicts(user_id, conflicts)
                    await asyncio.to_thread(
                        publish_event,
                        user_id,
                        {"type": "identity.conflict", "payload": conflicts},
                    )
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
                    idempotency_key=self._assistant_idempotency_key(idempotency_key),
                    sql_session=sql_session,
                ),
                "store_timeout_fallback",
            )
            result = {
                "response": fallback,
                "insights": {},
                "conflicts": [],
                "entities": [],
                "emotions": {},
            }
            self._cache_result(user_id, conversation_id, idempotency_key, result)
            return result
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
                        idempotency_key=self._assistant_idempotency_key(idempotency_key),
                        sql_session=sql_session,
                    ),
                    "store_llm_error_fallback",
                )
            except Exception:
                self.logger.exception("Failed to queue fallback assistant message for user %s", user_id)
            result = {
                "response": fallback,
                "insights": {},
                "conflicts": [],
                "entities": [],
                "emotions": {},
            }
            self._cache_result(user_id, conversation_id, idempotency_key, result)
            return result

        try:
            entities, emotions = await asyncio.gather(
                asyncio.to_thread(ds_service.extract_entities, message),
                asyncio.to_thread(ds_service.detect_emotions, message),
            )
        except Exception:
            self.logger.exception("DS inference failed for user %s", user_id)
            entities, emotions = [], {}

        _fire_and_forget(
            self.memory.store_conversation(
                user_id=user_id,
                role="user",
                content=message,
                conversation_id=conversation_id,
                metadata={
                    "emotions": emotions if isinstance(emotions, dict) else {},
                    "entities": entities if isinstance(entities, list) else [],
                    "logged_at": datetime.now(timezone.utc).isoformat(),
                },
                idempotency_key=idempotency_key,
                sql_session=sql_session,
            ),
            "store_user_message_with_metadata",
        )

        _fire_and_forget(
            self.memory.store_conversation(
                user_id=user_id,
                role="assistant",
                content=response,
                conversation_id=conversation_id,
                idempotency_key=self._assistant_idempotency_key(idempotency_key),
                sql_session=sql_session,
            ),
            "store_assistant_message",
        )

        conversation_data = {"user": message, "assistant": response}
        insights: Dict = {}

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

        result = {
            "response": response,
            "insights": insights or {},
            "conflicts": conflicts,
            "entities": entities if isinstance(entities, list) else [],
            "emotions": emotions if isinstance(emotions, dict) else {},
        }
        self._cache_result(user_id, conversation_id, idempotency_key, result)
        return result

    def _idempotency_cache_key(self, user_id: str, conversation_id: str, idempotency_key: str) -> str:
        return f"chat:idempotency:{user_id}:{conversation_id}:{idempotency_key}"

    def _assistant_idempotency_key(self, idempotency_key: str | None) -> str | None:
        if not idempotency_key:
            return None
        return f"{idempotency_key}:assistant"

    def _get_cached_result(
        self,
        user_id: str,
        conversation_id: str,
        idempotency_key: str | None,
    ) -> Dict | None:
        if not idempotency_key:
            return None
        try:
            cached = self.memory.cache.get(self._idempotency_cache_key(user_id, conversation_id, idempotency_key))
            if not cached:
                return None
            parsed = json.loads(cached)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            self.logger.warning("Failed to read idempotency cache for user %s", user_id, exc_info=True)
            return None

    def _cache_result(
        self,
        user_id: str,
        conversation_id: str,
        idempotency_key: str | None,
        result: Dict[str, Any],
    ) -> None:
        if not idempotency_key:
            return
        try:
            self.memory.cache.setex(
                self._idempotency_cache_key(user_id, conversation_id, idempotency_key),
                3600,
                json.dumps(result),
            )
        except Exception:
            self.logger.warning("Failed to write idempotency cache for user %s", user_id, exc_info=True)
