from typing import Any, Dict, List, Optional
import json
from contextlib import contextmanager
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session


class EmotionStore:
    def __init__(self):
        """
        Initialize the EmotionStore and configure its storage client.
        
        Sets self.supabase to a Supabase client when the application is using the non-SQL backend; sets it to None when the SQL backend is active.
        """
        self.supabase = get_db() if not has_sql() else None

    @contextmanager
    def _session_scope(self, session: Optional[Any]):
        if session is not None:
            yield session
        else:
            with get_sql_session() as new_session:
                yield new_session

    def load(self, user_id: str, identity_id: str, sql_session: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Load stored emotions for the specified user identity.
        """
        if has_sql():
            with self._session_scope(sql_session) as session:
                result = session.execute(
                    text(
                        """
                        SELECT primary_emotion, intensity, secondary_emotions, context
                        FROM identity_emotions
                        WHERE user_id = :user_id
                          AND identity_id = :identity_id
                        ORDER BY created_at ASC
                        """
                    ),
                    {"user_id": user_id, "identity_id": identity_id},
                )
                rows = [dict(row) for row in result.mappings().all()]
                for row in rows:
                    for field in ("secondary_emotions", "context"):
                        if isinstance(row.get(field), str):
                            try:
                                row[field] = json.loads(row[field])
                            except (json.JSONDecodeError, TypeError):
                                pass
                return rows

        if not self.supabase:
            return []

        response = (
            self.supabase.table("identity_emotions")
            .select("primary_emotion, intensity, secondary_emotions, context")
            .eq("user_id", user_id)
            .eq("identity_id", identity_id)
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []

    def replace(self, user_id: str, identity_id: str, emotions: List[Dict[str, Any]], sql_session: Optional[Any] = None) -> None:
        """
        Replace all stored emotions for the given user and identity with the provided list.
        """
        if has_sql():
            with self._session_scope(sql_session) as session:
                session.execute(
                    text(
                        """
                        DELETE FROM identity_emotions
                        WHERE user_id = :user_id
                          AND identity_id = :identity_id
                        """
                    ),
                    {"user_id": user_id, "identity_id": identity_id},
                )
                for emotion in emotions:
                    session.execute(
                        text(
                            """
                            INSERT INTO identity_emotions (
                                identity_id, user_id, primary_emotion, intensity, secondary_emotions, context
                            ) VALUES (
                                :identity_id, :user_id, :primary_emotion, :intensity, :secondary_emotions, :context
                            )
                            """
                        ),
                        {
                            "identity_id": identity_id,
                            "user_id": user_id,
                            "primary_emotion": emotion.get("primary_emotion", ""),
                            "intensity": emotion.get("intensity", 0.5),
                            "secondary_emotions": json.dumps(emotion.get("secondary_emotions", [])),
                            "context": json.dumps(emotion.get("context", {})),
                        },
                    )
                if sql_session is None:
                    session.commit()
            return

        if not self.supabase:
            return

        self.supabase.table("identity_emotions").delete().eq("user_id", user_id).eq(
            "identity_id", identity_id
        ).execute()

        if not emotions:
            return

        payload = []
        for emotion in emotions:
            payload.append(
                {
                    "identity_id": identity_id,
                    "user_id": user_id,
                    "primary_emotion": emotion.get("primary_emotion", ""),
                    "intensity": emotion.get("intensity", 0.5),
                    "secondary_emotions": emotion.get("secondary_emotions", []),
                    "context": emotion.get("context", {}),
                }
            )

        self.supabase.table("identity_emotions").insert(payload).execute()
