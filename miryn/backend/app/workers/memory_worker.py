import asyncio
from datetime import datetime, timedelta
from sqlalchemy import text
from app.workers.celery_app import celery_app
from app.core.database import get_db, has_sql, get_sql_session
from app.services.llm_service import LLMService
from app.core.encryption import decrypt_text


@celery_app.task(name="memory.gc")
def garbage_collect_expired():
    """
    Remove messages whose `delete_at` timestamp is less than or equal to the current UTC time.
    
    This operation supports both SQL and non-SQL backends and will delete all messages with a non-null `delete_at` due at or before the time of invocation.
    
    Returns:
        dict: `{'deleted': True}` if the deletion operation was executed.
    """
    now = datetime.utcnow()
    if has_sql():
        with get_sql_session() as session:
            session.execute(
                text("DELETE FROM messages WHERE delete_at IS NOT NULL AND delete_at <= :now"),
                {"now": now},
            )
            session.commit()
        return {"deleted": True}

    db = get_db()
    db.table("messages").delete().lte("delete_at", now.isoformat()).execute()
    return {"deleted": True}


@celery_app.task(name="memory.summarize")
def nightly_summarize():
    """
    Generate and store daily per-user summaries of messages from the last 24 hours.
    
    This task collects up to 200 messages per user created within the past 24 hours, decrypts content when necessary, uses an LLMService to produce a concise summary for each user, and inserts the summary into the memory_summaries store with the current UTC timestamp. Works with either SQL or non-SQL backends.
    
    Returns:
        dict: A mapping with the key "summaries" and an integer value for the number of user summaries processed.
    """
    llm = LLMService()
    cutoff = datetime.utcnow() - timedelta(days=1)

    if has_sql():
        with get_sql_session() as session:
            users = session.execute(
                text(
                    """
                    SELECT DISTINCT user_id
                    FROM messages
                    WHERE created_at >= :cutoff
                    """
                ),
                {"cutoff": cutoff},
            ).scalars().all()
        for user_id in users:
            with get_sql_session() as session:
                rows = session.execute(
                    text(
                        """
                        SELECT content, content_encrypted
                        FROM messages
                        WHERE user_id = :user_id
                          AND created_at >= :cutoff
                        ORDER BY created_at ASC
                        LIMIT 200
                        """
                    ),
                    {"user_id": user_id, "cutoff": cutoff},
                ).mappings().all()
            content = []
            for row in rows:
                text_content = row.get("content") or decrypt_text(row.get("content_encrypted"))
                if text_content:
                    content.append(text_content)
            summary = asyncio.run(_summarize(llm, content))
            if summary:
                with get_sql_session() as session:
                    session.execute(
                        text(
                            """
                            INSERT INTO memory_summaries (user_id, summary, created_at)
                            VALUES (:user_id, :summary, :created_at)
                            """
                        ),
                        {"user_id": user_id, "summary": summary, "created_at": datetime.utcnow()},
                    )
                    session.commit()
        return {"summaries": len(users)}

    db = get_db()
    users_resp = (
        db.table("messages")
        .select("user_id")
        .gte("created_at", cutoff.isoformat())
        .execute()
    )
    user_ids = list({row.get("user_id") for row in (users_resp.data or []) if row.get("user_id")})
    for user_id in user_ids:
        messages = (
            db.table("messages")
            .select("content, content_encrypted")
            .eq("user_id", user_id)
            .gte("created_at", cutoff.isoformat())
            .limit(200)
            .execute()
        )
        content = []
        for m in (messages.data or []):
            text_content = m.get("content") or decrypt_text(m.get("content_encrypted"))
            if text_content:
                content.append(text_content)
        summary = asyncio.run(_summarize(llm, content))
        if summary:
            db.table("memory_summaries").insert(
                {"user_id": user_id, "summary": summary, "created_at": datetime.utcnow().isoformat()}
            ).execute()
    return {"summaries": len(user_ids)}


async def _summarize(llm: LLMService, messages: list) -> str:
    """
    Produce a short 3–5 bullet summary of the provided messages that highlights goals, concerns, and key events.
    
    Parameters:
    	llm (LLMService): LLM client used to generate the summary.
    	messages (list): List of message strings to summarize.
    
    Returns:
    	summary (str): Summary text containing 3–5 concise bullets, or an empty string if `messages` is empty.
    """
    if not messages:
        return ""
    prompt = (
        "Summarize the user's last 24h of conversation in 3-5 concise bullets. "
        "Focus on goals, concerns, and key events.\n\n"
        f"Messages:\n{messages}"
    )
    return await llm.generate(prompt, max_tokens=300)
