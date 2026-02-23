from typing import Dict
import logging
from app.services.identity_engine import IdentityEngine
from app.services.memory_layer import MemoryLayer
from app.services.reflection_engine import ReflectionEngine
from app.services.llm_service import LLMService
from app.core.cache import publish_event
from app.workers.reflection_worker import analyze_reflection


class ConversationOrchestrator:
    def __init__(self):
        self.llm = LLMService()
        self.identity = IdentityEngine()
        self.memory = MemoryLayer()
        self.reflection = ReflectionEngine(self.llm)
        self.logger = logging.getLogger(__name__)

    async def handle_message(self, user_id: str, message: str, conversation_id: str) -> Dict:
        identity = self.identity.get_identity(user_id)

        memories = await self.memory.retrieve_context(
            user_id=user_id,
            query=message,
            limit=5,
            strategy="hybrid",
            conversation_id=conversation_id,
        )

        context = {
            "identity": identity,
            "memories": memories,
            "patterns": {},
        }

        await self.memory.store_conversation(
            user_id=user_id,
            role="user",
            content=message,
            conversation_id=conversation_id,
        )

        conflicts = []
        try:
            conflicts = await self.reflection.detect_contradictions(
                identity.get("beliefs", []),
                message,
            )
            if conflicts:
                self.identity.add_conflicts(user_id, conflicts)
                publish_event(user_id, {"type": "identity.conflict", "payload": conflicts})
        except Exception:
            self.logger.exception("Conflict detection failed for user %s", user_id)

        try:
            response = await self.llm.chat(
                context=context,
                user_message=message,
                identity=identity,
            )
        except Exception:
            self.logger.exception("LLM chat failed for user %s", user_id)
            fallback = "I'm having trouble responding right now. Please try again shortly."
            try:
                await self.memory.store_conversation(
                    user_id=user_id,
                    role="assistant",
                    content=fallback,
                    conversation_id=conversation_id,
                )
            except Exception:
                self.logger.exception("Failed to persist fallback assistant message for user %s", user_id)
            return {
                "response": fallback,
                "insights": {},
            }

        try:
            await self.memory.store_conversation(
                user_id=user_id,
                role="assistant",
                content=response,
                conversation_id=conversation_id,
            )
        except Exception:
            self.logger.exception("Failed to persist assistant message for user %s", user_id)

        conversation_data = {"user": message, "assistant": response}
        insights: Dict = {}
        try:
            insights = await self.reflection.analyze_conversation(
                user_id=user_id,
                conversation=conversation_data,
            )
        except Exception:
            self.logger.exception("Reflection analysis failed for user %s", user_id)

        try:
            analyze_reflection.delay(user_id, conversation_data)
            publish_event(user_id, {"type": "reflection.queued"})
        except Exception:
            self.logger.exception("Failed to queue reflection task for user %s", user_id)

        return {
            "response": response,
            "insights": insights,
            "conflicts": conflicts,
        }
