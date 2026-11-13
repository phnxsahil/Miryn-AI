import json
import logging
from app.services.reflection_engine import ReflectionEngine
from app.services.identity_engine import IdentityEngine
from app.services.llm_service import LLMService
from app.core.cache import redis_client

logger = logging.getLogger(__name__)

llm = LLMService()
reflection = ReflectionEngine(llm)
identity = IdentityEngine()

def _extract_messages(conv: dict) -> list:
    messages = []
    mapping = conv.get("mapping", {})
    for node in mapping.values():
        msg = node.get("message")
        if not msg:
            continue
        role = msg.get("author", {}).get("role", "")
        if role not in ("user", "assistant"):
            continue
        parts = msg.get("content", {}).get("parts", [])
        content = " ".join(str(p) for p in parts if isinstance(p, str))
        if content.strip():
            messages.append({"role": role, "content": content})
    return messages

async def process_chatgpt_import(user_id: str, raw_content: bytes):
    try:
        redis_client.setex(
            f"import_status:{user_id}",
            3600,
            json.dumps({"status": "processing", "progress": 0})
        )
        
        conversations = json.loads(raw_content)
        total = len(conversations)
        memories_added = 0
        
        # Cap at 100 conversations
        process_limit = min(total, 100)
        
        for i, conv in enumerate(conversations[:process_limit]):
            messages = _extract_messages(conv)
            if not messages:
                continue
                
            # Combine messages for ReflectionEngine.analyze_conversation
            # which expects a Dict with "user" and "assistant" keys
            user_text = " ".join([m["content"] for m in messages if m["role"] == "user"])
            assistant_text = " ".join([m["content"] for m in messages if m["role"] == "assistant"])
            
            conv_payload = {
                "user": user_text,
                "assistant": assistant_text
            }
            
            result = await reflection.analyze_conversation(
                user_id=user_id,
                conversation=conv_payload
            )
            
            # 1. Update emotions
            emotions = result.get("emotions") or {}
            if emotions.get("primary_emotion"):
                identity.update_identity(user_id, {"emotions": [emotions]})
            
            # 2. Track open loops (only items the model marked unresolved)
            for loop in result.get("open_loops") or []:
                identity.track_open_loop(user_id, loop["topic"], importance=loop.get("importance", 1))
            
            memories_added += 1
            
            # Update progress
            progress = int((i + 1) / process_limit * 100)
            redis_client.setex(
                f"import_status:{user_id}",
                3600,
                json.dumps({"status": "processing", "progress": progress})
            )
            
        redis_client.setex(
            f"import_status:{user_id}",
            3600,
            json.dumps({
                "status": "complete",
                "conversations_processed": process_limit,
                "memories_added": memories_added,
            })
        )
        
    except Exception as e:
        logger.error(f"Error processing ChatGPT import for user {user_id}: {e}", exc_info=True)
        redis_client.setex(
            f"import_status:{user_id}",
            3600,
            json.dumps({"status": "error", "message": str(e)[:200]})
        )

async def process_gemini_import(user_id: str, raw_content: bytes):
    try:
        redis_client.setex(
            f"import_status:{user_id}",
            3600,
            json.dumps({"status": "processing", "progress": 0})
        )
        
        data = json.loads(raw_content)
        messages = []
        
        # Extract user prompts from Gemini export (My Activity)
        for item in data:
            for detail in item.get("details", []):
                text = detail.get("activityValue", {}).get("stringValue", "")
                if text.strip():
                    messages.append({"role": "user", "content": text})
        
        # Batch into fake conversations of 20 messages each to keep context relevant
        batch_size = 20
        # Cap at 2000 total messages (100 batches)
        max_messages = min(len(messages), 2000)
        total_batches = (max_messages + batch_size - 1) // batch_size
        
        memories_added = 0
        
        for i in range(0, max_messages, batch_size):
            batch = messages[i:i+batch_size]
            user_text = " ".join([m["content"] for m in batch])
            
            # Since Gemini My Activity usually only has user side
            conv_payload = {
                "user": user_text,
                "assistant": ""
            }
            
            result = await reflection.analyze_conversation(
                user_id=user_id,
                conversation=conv_payload
            )
            
            # 1. Update emotions
            emotions = result.get("emotions") or {}
            if emotions.get("primary_emotion") and emotions["primary_emotion"] != "neutral":
                identity.update_identity(user_id, {"emotions": [emotions]})
            
            # 2. Track open loops (only items the model marked unresolved)
            for loop in result.get("open_loops") or []:
                identity.track_open_loop(user_id, loop["topic"], importance=loop.get("importance", 1))
                
            memories_added += 1
            
            # Update progress
            current_batch = i // batch_size + 1
            progress = int(current_batch / total_batches * 100)
            redis_client.setex(
                f"import_status:{user_id}",
                3600,
                json.dumps({"status": "processing", "progress": progress})
            )
            
        redis_client.setex(
            f"import_status:{user_id}",
            3600,
            json.dumps({
                "status": "complete",
                "conversations_processed": total_batches,
                "memories_added": memories_added,
            })
        )
        
    except Exception as e:
        logger.error(f"Error processing Gemini import for user {user_id}: {e}", exc_info=True)
        redis_client.setex(
            f"import_status:{user_id}",
            3600,
            json.dumps({"status": "error", "message": str(e)[:200]})
        )
