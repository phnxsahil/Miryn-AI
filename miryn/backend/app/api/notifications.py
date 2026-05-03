from fastapi import APIRouter, Depends
from datetime import datetime, timezone
import json
import logging
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session
from app.core.security import get_current_user_id
from app.schemas.notifications import NotificationPreferences

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)


@router.patch("/preferences")
def update_preferences(payload: NotificationPreferences, user_id: str = Depends(get_current_user_id)):
    prefs = {
        "checkin_reminders": payload.checkin_reminders,
        "weekly_digest": payload.weekly_digest,
        "browser_push": payload.browser_push,
    }
    
    if has_sql():
        with get_sql_session() as session:
            session.execute(
                text(
                    """
                    UPDATE users
                    SET notification_preferences = :prefs,
                        data_retention = :retention
                    WHERE id = :user_id
                    """
                ),
                {
                    "prefs": json.dumps(prefs),
                    "retention": payload.data_retention,
                    "user_id": user_id
                },
            )
            session.commit()
    else:
        db = get_db()
        db.table("users").update({
            "notification_preferences": prefs,
            "data_retention": payload.data_retention
        }).eq("id", user_id).execute()
        
    return {"message": "Preferences updated"}


@router.get("/")
def list_notifications(user_id: str = Depends(get_current_user_id)):
    """
    Retrieve up to 50 most recent notifications for the current user.
    
    Parameters:
    	user_id (str): ID of the current authenticated user.
    
    Returns:
    	notifications (list[dict]): List of notification objects (may be empty). Each dict contains the keys:
    		`id`, `type`, `payload`, `status`, `created_at`, and `read_at`.
    """
    if has_sql():
        try:
            with get_sql_session() as session:
                rows = session.execute(
                    text(
                        """
                        SELECT id, type, payload, status, created_at, read_at
                        FROM notifications
                        WHERE user_id = :user_id
                        ORDER BY created_at DESC
                        LIMIT 50
                        """
                    ),
                    {"user_id": user_id},
                )
                return [dict(row) for row in rows.mappings().all()]
        except Exception as exc:
            logger.warning("Notifications SQL query failed; returning empty list: %s", exc)
            return []

    db = get_db()
    response = (
        db.table("notifications")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return response.data or []


@router.post("/read/{notification_id}")
def mark_read(notification_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Mark a notification as read for the current user.
    
    Parameters:
        notification_id (str): ID of the notification to mark as read.
    
    Returns:
        dict: {"status": "ok"} on success.
    """
    if has_sql():
        try:
            with get_sql_session() as session:
                session.execute(
                    text(
                        """
                        UPDATE notifications
                        SET status = 'read', read_at = NOW()
                        WHERE id = :id AND user_id = :user_id
                        """
                    ),
                    {"id": notification_id, "user_id": user_id},
                )
                session.commit()
        except Exception as exc:
            logger.warning("Notifications mark-read failed; no-op in demo mode: %s", exc)
        return {"status": "ok"}

    db = get_db()
    db.table("notifications").update({"status": "read", "read_at": datetime.now(timezone.utc).isoformat()}).eq("id", notification_id).eq("user_id", user_id).execute()
    return {"status": "ok"}
