from typing import Any, Dict, List
import json
from sqlalchemy import text
from app.core.database import get_db, has_sql, get_sql_session


class EmotionStore:
    def __init__(self):
        """
        Initialize the EmotionStore and configure its storage client.
        
        Sets self.supabase to a Supabase client when the application is using the non-SQL backend; sets it to None when the SQL backend is active.
        """
        self.supabase = get_db() if not has_sql() else None

    def load(self, user_id: str, identity_id: str) -> List[Dict[str, Any]]:
        """
        Load stored emotions for the specified user identity.
        
        Fetches emotion records from the configured storage backend and returns them ordered by creation time (oldest first).
        
        Returns:
            A list of dictionaries, each containing:
                - primary_emotion (str): The main emotion label.
                - intensity (float): The intensity value for the primary emotion.
                - secondary_emotions (list): A list of secondary emotion labels.
                - context (dict): Arbitrary contextual data associated with the record.
            Returns an empty list if no records are found or if no backend is available.
        """
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
        """
        Replace all stored emotions for the given user and identity with the provided list.
        
        Deletes any existing rows for the (user_id, identity_id) pair and inserts the provided emotions in their place. If `emotions` is empty the existing records are removed and nothing is inserted. If the SQL backend is used, `secondary_emotions` and `context` are JSON-serialized before insertion.
        
        Parameters:
            user_id (str): ID of the user who owns the identity.
            identity_id (str): ID of the identity whose emotions are being replaced.
            emotions (List[Dict[str, Any]]): List of emotion objects to store. Each object may include:
                - "primary_emotion" (str): Primary emotion (defaults to "").
                - "intensity" (float): Emotion intensity (defaults to 0.5).
                - "secondary_emotions" (List): List of secondary emotions (defaults to []).
                - "context" (Dict): Arbitrary context data (defaults to {}).
        """
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
