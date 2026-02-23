import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import text

from app.core.cache import publish_event, enqueue_job
from app.core.database import get_db, has_sql, get_sql_session


class OutreachScheduler:
    def __init__(self):
        self.threshold_days = 2

    def scan(self) -> int:
        cutoff = datetime.utcnow() - timedelta(days=self.threshold_days)
        if has_sql():
            with get_sql_session() as session:
                rows = session.execute(
                    text(
                        """
                        SELECT user_id, topic, last_mentioned
                        FROM identity_open_loops
                        WHERE status = 'open'
                          AND (last_mentioned IS NULL OR last_mentioned <= :cutoff)
                        """
                    ),
                    {"cutoff": cutoff},
                ).mappings().all()
                pattern_rows = session.execute(
                    text(
                        """
                        SELECT user_id, pattern_type, description, confidence
                        FROM identity_patterns
                        WHERE confidence >= 0.7
                        """
                    )
                ).mappings().all()
            notifications = self._build_notifications(rows, pattern_rows)
            if notifications:
                with get_sql_session() as session:
                    for note in notifications:
                        session.execute(
                            text(
                                """
                                INSERT INTO notifications (user_id, type, payload, status, created_at)
                                VALUES (:user_id, :type, :payload, :status, :created_at)
                                """
                            ),
                            self._prepare_sql_note(note),
                        )
                    session.commit()
            for note in notifications:
                publish_event(note["user_id"], {"type": "notification.new", "payload": note})
                enqueue_job("outreach", note)
            return len(notifications)

        db = get_db()
        response = (
            db.table("identity_open_loops")
            .select("user_id, topic, last_mentioned")
            .eq("status", "open")
            .execute()
        )
        rows = [row for row in (response.data or []) if row]
        filtered = []
        for row in rows:
            last = row.get("last_mentioned")
            if not last:
                filtered.append(row)
                continue
            try:
                if datetime.fromisoformat(str(last).replace("Z", "+00:00")) <= cutoff:
                    filtered.append(row)
            except Exception:
                continue
        pattern_response = db.table("identity_patterns").select("user_id, pattern_type, description, confidence").execute()
        pattern_rows = [
            row for row in (pattern_response.data or []) if row and (row.get("confidence", 0) >= 0.7)
        ]
        notifications = self._build_notifications(filtered, pattern_rows)
        if notifications:
            serialized = self._serialize_notifications(notifications)
            db.table("notifications").insert(serialized).execute()
        for note in notifications:
            publish_event(note["user_id"], {"type": "notification.new", "payload": note})
            enqueue_job("outreach", note)
        return len(notifications)

    def _build_notifications(self, rows: List[Dict], pattern_rows: List[Dict]) -> List[Dict]:
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
        payload = note.get("payload") or {}
        return {
            **note,
            "payload": json.dumps(payload),
        }

    def _serialize_notifications(self, notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
