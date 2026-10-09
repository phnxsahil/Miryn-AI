import asyncio
import json
import logging
from datetime import datetime

from sqlalchemy import text

from app.core.cache import publish_event
from app.core.database import get_db, get_sql_session, has_sql
from app.services.email_service import send_checkin
from app.services.llm_service import LLMService, QuotaExhausted
from app.services.outreach_scheduler import OutreachScheduler
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
llm = LLMService()

async def generate_checkin_message(user_id: str, loop_topic: str) -> str:
    """
    Generate a personalized check-in message using LLM.
    """
    if LLMService.quota_dead():
        logger.info("Skipping outreach generation for user %s while Gemini quota cooldown is active", user_id)
        return ""
    prompt = f"""You are Miryn checking in with a user.
They mentioned "{loop_topic}" in a past conversation but never resolved it.
Write a single warm, natural opening message (2-3 sentences max) to reconnect.
Don't be pushy. Just open the door.
Return only the message text, nothing else."""
    try:
        return await llm.generate(prompt)
    except QuotaExhausted:
        logger.info("Skipping outreach generation for user %s after Gemini quota exhaustion", user_id)
        return ""

async def process_outreach():
    """
    Find stale loops, generate personalized messages, and send them.
    """
    if LLMService.quota_dead():
        logger.info("Skipping outreach while Gemini quota cooldown is active")
        return 0

    scheduler = OutreachScheduler()
    discovered_items = scheduler.scan()
    
    count = 0
    for item in discovered_items:
        try:
            user_id = item["user_id"]
            user_email = item["user_email"]
            
            # 1. Generate message
            if item["type"] == "open_loop":
                topic = item["topic"]
                message = await generate_checkin_message(user_id, topic)
                if not message:
                    continue
                note_type = "open_loop_followup"
                payload = {"topic": topic, "message": message}
            else:
                # Pattern followup
                desc = item["description"]
                message = f"I've been noticing a pattern: {desc}. Just wanted to check in and see how you're feeling about it."
                note_type = "pattern_followup"
                payload = {"pattern": desc, "message": message}

            # 2. Send email
            send_checkin(user_email, message)

            # 3. Create notification in DB
            notification = {
                "user_id": user_id,
                "type": note_type,
                "payload": payload,
                "status": "new",
                "created_at": datetime.utcnow()
            }

            if has_sql():
                with get_sql_session() as session:
                    session.execute(
                        text(
                            """
                            INSERT INTO notifications (user_id, type, payload, status, created_at)
                            VALUES (:user_id, :type, :payload, :status, :created_at)
                            """
                        ),
                        {
                            **notification,
                            "payload": json.dumps(payload)
                        },
                    )
                    session.commit()
            else:
                db = get_db()
                db.table("notifications").insert({
                    **notification,
                    "created_at": notification["created_at"].isoformat()
                }).execute()

            # 4. Publish event for real-time UI
            publish_event(user_id, {"type": "notification.new", "payload": notification})
            count += 1
            
        except Exception as exc:
            logger.error("Failed to process outreach for item %s: %s", item, exc, exc_info=True)

    return count

@celery_app.task(name="outreach.scan")
def scan_outreach():
    """
    Celery task wrapper for the outreach process.
    """
    return {"notifications": asyncio.run(process_outreach())}
