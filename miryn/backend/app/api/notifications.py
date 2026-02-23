from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session
from app.core.security import get_current_user_id

router = APIRouter(prefix="/notifications", tags=["notifications"])


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
        return {"status": "ok"}

    db = get_db()
    db.table("notifications").update({"status": "read"}).eq("id", notification_id).eq("user_id", user_id).execute()
    return {"status": "ok"}
