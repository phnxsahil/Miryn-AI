import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import text

from app.core.database import get_db, has_sql, get_sql_session


class OutreachScheduler:
    def __init__(self):
        """
        Initialize the outreach scheduler and set the default cutoff window.
        
        Sets `threshold_days` to 2, the default number of days used as the cutoff when determining whether an open loop's `last_mentioned` timestamp is old enough to trigger a follow-up.
        """
        self.threshold_days = 2

    def scan(self) -> List[Dict]:
        """
        Scan for stale open loops and high-confidence identity patterns.
        Fetches user emails to facilitate direct outreach.
        
        Returns:
            List[Dict]: A list of discovered items (loops and patterns) with user metadata.
        """
        cutoff = datetime.utcnow() - timedelta(days=self.threshold_days)
        discovered = []

        if has_sql():
            with get_sql_session() as session:
                # Join with users table to get email
                rows = session.execute(
                    text(
                        """
                        SELECT l.user_id, l.topic, l.last_mentioned, u.email
                        FROM identity_open_loops l
                        JOIN users u ON l.user_id = u.id
                        WHERE l.status = 'open'
                          AND (l.last_mentioned IS NULL OR l.last_mentioned <= :cutoff)
                        """
                    ),
                    {"cutoff": cutoff},
                ).mappings().all()
                
                for row in rows:
                    discovered.append({
                        "user_id": str(row["user_id"]),
                        "user_email": row["email"],
                        "type": "open_loop",
                        "topic": row["topic"]
                    })

                pattern_rows = session.execute(
                    text(
                        """
                        SELECT p.user_id, p.pattern_type, p.description, p.confidence, u.email
                        FROM identity_patterns p
                        JOIN users u ON p.user_id = u.id
                        WHERE p.confidence >= 0.7
                        """
                    )
                ).mappings().all()
                
                for row in pattern_rows:
                    discovered.append({
                        "user_id": str(row["user_id"]),
                        "user_email": row["email"],
                        "type": "pattern",
                        "description": row["description"] or row["pattern_type"]
                    })
            return discovered

        db = get_db()
        # Supabase path
        response = (
            db.table("identity_open_loops")
            .select("user_id, topic, last_mentioned")
            .eq("status", "open")
            .execute()
        )
        loops = response.data or []
        
        for loop in loops:
            last = loop.get("last_mentioned")
            is_stale = False
            if not last:
                is_stale = True
            else:
                try:
                    if datetime.fromisoformat(str(last).replace("Z", "+00:00")) <= cutoff:
                        is_stale = True
                except Exception:
                    continue
            
            if is_stale:
                # Fetch user email
                user_res = db.table("users").select("email").eq("id", loop["user_id"]).single().execute()
                email = user_res.data.get("email") if user_res.data else "unknown@example.com"
                discovered.append({
                    "user_id": loop["user_id"],
                    "user_email": email,
                    "type": "open_loop",
                    "topic": loop["topic"]
                })

        pattern_res = db.table("identity_patterns").select("user_id, pattern_type, description, confidence").execute()
        patterns = [p for p in (pattern_res.data or []) if p.get("confidence", 0) >= 0.7]
        
        for p in patterns:
            user_res = db.table("users").select("email").eq("id", p["user_id"]).single().execute()
            email = user_res.data.get("email") if user_res.data else "unknown@example.com"
            discovered.append({
                "user_id": p["user_id"],
                "user_email": email,
                "type": "pattern",
                "description": p["description"] or p["pattern_type"]
            })
            
        return discovered

    def _build_notifications(self, rows: List[Dict], pattern_rows: List[Dict]) -> List[Dict]:
        """
        Builds notification dictionaries for open-loop followups and pattern followups.
        
        Parameters:
            rows (List[Dict]): Iterable of open-loop records; each record should include at least `user_id` and `topic`.
            pattern_rows (List[Dict]): Iterable of pattern records; each record should include at least `user_id` and either `description` or `pattern_type`.
        
        Returns:
            List[Dict]: A list of notification objects. Each notification contains:
                - `user_id` (str): target user identifier
                - `type` (str): either `"open_loop_followup"` or `"pattern_followup"`
                - `payload` (Dict): context for the notification (includes `topic` or `pattern` and a `message`)
                - `status` (str): `"new"`
                - `created_at` (datetime): UTC timestamp when the notification was created
        """
        notifications = []
        for row in rows:
            user_id = row.get("user_id")
            topic = row.get("topic")
            if not user_id or not topic:
                continue
            payload = {"topic": topic, "message": f"Checking in on: {topic}"}
            notifications.append(
                {
                    "user_id": user_id,
                    "type": "open_loop_followup",
                    "payload": payload,
                    "status": "new",
                    "created_at": datetime.utcnow(),
                }
            )
        for row in pattern_rows:
            user_id = row.get("user_id")
            description = row.get("description") or row.get("pattern_type")
            if not user_id or not description:
                continue
            payload = {"pattern": description, "message": f"Noticing a pattern: {description}"}
            notifications.append(
                {
                    "user_id": user_id,
                    "type": "pattern_followup",
                    "payload": payload,
                    "status": "new",
                    "created_at": datetime.utcnow(),
                }
            )
        return notifications

    def _prepare_sql_note(self, note: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize the `payload` field of a notification dict into a JSON string for SQL insertion.
        
        Parameters:
            note (Dict[str, Any]): Notification dictionary; may contain a `payload` value (any JSON-serializable object).
        
        Returns:
            Dict[str, Any]: A copy of `note` where `payload` is replaced by its JSON string representation (empty object serialized if `payload` was missing or falsy).
        """
        payload = note.get("payload") or {}
        return {
            **note,
            "payload": json.dumps(payload),
        }

    def _serialize_notifications(self, notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert a list of notification dicts into a database-serializable form.
        
        Parameters:
            notes (List[Dict[str, Any]]): Notification dictionaries that may contain a `payload` value and a `created_at` value (a datetime or already-serializable value).
        
        Returns:
            List[Dict[str, Any]]: A new list where each notification has a `payload` (defaults to an empty dict if missing or falsy) and `created_at` converted to an ISO 8601 string if it was a `datetime`, otherwise left unchanged.
        """
        serialized: List[Dict[str, Any]] = []
        for note in notes:
            created_at = note.get("created_at")
            serialized.append(
                {
                    **note,
                    "payload": note.get("payload") or {},
                    "created_at": created_at.isoformat() if isinstance(created_at, datetime) else created_at,
                }
            )
        return serialized
