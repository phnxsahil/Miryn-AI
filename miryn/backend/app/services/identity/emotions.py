from typing import Any, Dict, List
import json
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session


class EmotionStore:
    def __init__(self):
        self.supabase = get_db() if not has_sql() else None

    def load(self, user_id: str, identity_id: str) -> List[Dict[str, Any]]:
        if has_sql():
            with get_sql_session() as session:
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
                return [dict(row) for row in result.mappings().all()]

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

    def replace(self, user_id: str, identity_id: str, emotions: List[Dict[str, Any]]) -> None:
        if has_sql():
            with get_sql_session() as session:
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
